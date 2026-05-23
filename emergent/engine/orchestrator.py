import asyncio
import logging
import signal
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from emergent.db.models import Agent, AgentTurn, SimulationSession, Speech, ToolCall
from emergent.agents.state import AgentStateManager
from emergent.agents.memory import MemoryManager
from emergent.engine.context import ContextBuilder
from emergent.engine.reactions import handle_reactions
from emergent.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(
        self,
        db: AsyncSession,
        registry: ToolRegistry,
        state_mgr: AgentStateManager,
        memory_mgr: MemoryManager,
        context_builder: ContextBuilder,
        provider,
        session_id: uuid.UUID,
    ):
        self.db = db
        self.registry = registry
        self.state_mgr = state_mgr
        self.memory_mgr = memory_mgr
        self.context_builder = context_builder
        self.provider = provider
        self.session_id = session_id
        self._running = False
        self._turn_number = 0

    async def initialize_simulation(self, world_path: str, name: str):
        session = SimulationSession(
            id=self.session_id,
            name=name,
            world_path=world_path,
            status="running",
        )
        self.db.add(session)
        await self.db.flush()
        self._turn_number = 0
        return session

    async def recover(self) -> Optional[SimulationSession]:
        result = await self.db.execute(
            select(SimulationSession).where(SimulationSession.id == self.session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            return None
        if session.status == "running":
            await self.db.execute(
                update(AgentTurn)
                .where(
                    AgentTurn.session_id == self.session_id,
                    AgentTurn.state == "in_progress",
                )
                .values(state="interrupted")
            )
            await self.db.flush()
        self._turn_number = session.current_turn_number
        return session

    async def run_turn(self, agent: Agent, turn_type: str = "regular") -> dict:
        turn = AgentTurn(
            session_id=self.session_id,
            agent_id=agent.id,
            turn_number=self._turn_number,
            state="in_progress",
            turn_type=turn_type,
        )
        self.db.add(turn)
        await self.db.flush()

        await self.state_mgr.apply_needs_decay(agent)

        ctx = await self.context_builder.assemble(agent)

        response = await self.provider.generate(
            system_prompt=ctx["system_prompt"],
            messages=[],
            tools=ctx["tools"],
            agent=agent,
        )

        tool_results = []
        for tc in response.tool_calls:
            tool = self.registry.get(tc.name)
            if not tool:
                continue
            try:
                existing = await self.db.execute(
                    select(ToolCall).where(ToolCall.id == uuid.UUID(tc.id))
                )
                existing_call = existing.scalar_one_or_none()
                if existing_call:
                    tool_results.append(existing_call.result)
                    continue
            except (ValueError, AttributeError):
                pass
            result = await tool.execute(agent, tc.params, self.db, self.provider)
            call = ToolCall(
                id=uuid.uuid4(),
                turn_id=turn.id,
                tool_name=tc.name,
                params=tc.params,
                result={"success": result.success, "data": result.data, "observation": result.observation},
            )
            self.db.add(call)
            tool_results.append(result)
            await self.db.flush()

            if tc.name == "say_to_agent":
                msg = tc.params.get("message", "")
                self.db.add(Speech(
                    agent_id=agent.id,
                    message=msg,
                    channel="say",
                    location_id=agent.current_location_id,
                ))
                await self.db.flush()
                await handle_reactions(
                    agent, msg,
                    self.db, self.registry, self.state_mgr, self.memory_mgr,
                    self.context_builder, self.provider,
                )

        await self.db.flush()

        turn.state = "completed"
        await self.db.flush()
        self._turn_number += 1
        await self.db.execute(
            update(SimulationSession)
            .where(SimulationSession.id == self.session_id)
            .values(
                current_turn_number=self._turn_number,
            )
        )
        await self.db.commit()
        return {
            "agent": agent.name,
            "turn_number": turn.turn_number,
            "response": response.content,
            "tool_calls": len(response.tool_calls),
            "tool_results": tool_results,
        }

    async def run_simulation(self, duration_seconds: Optional[int] = None):
        self._running = True
        start_time = datetime.now(timezone.utc)

        loop = asyncio.get_running_loop()
        stop_event = asyncio.Event()

        def _signal_handler():
            stop_event.set()

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, _signal_handler)
            except NotImplementedError:
                pass

        try:
            while self._running and not stop_event.is_set():
                if duration_seconds:
                    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
                    if elapsed >= duration_seconds:
                        break

                agents = await self.state_mgr.get_living_agents()
                if not agents:
                    logger.info("No living agents -- ending simulation")
                    break

                for agent in agents:
                    if stop_event.is_set():
                        break
                    result = await self.run_turn(agent)
                    logger.info(
                        f"[Turn {result['turn_number']}] {result['agent']}: "
                        f"{result['tool_calls']} tool calls"
                    )

            await self.db.commit()

        finally:
            self._running = False
            await self.db.execute(
                update(SimulationSession)
                .where(SimulationSession.id == self.session_id)
                .values(
                    status="paused",
                    completed_at=datetime.now(timezone.utc),
                )
            )
            await self.db.commit()

    async def graceful_shutdown(self):
        self._running = False
        await self.db.execute(
            update(SimulationSession)
            .where(SimulationSession.id == self.session_id)
            .values(
                status="paused",
                completed_at=datetime.now(timezone.utc),
            )
        )
        await self.db.commit()
