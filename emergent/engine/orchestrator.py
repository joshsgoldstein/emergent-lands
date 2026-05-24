import asyncio
import logging
import signal
import uuid
from datetime import datetime, timezone
from typing import Optional

import random
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from emergent.db.models import Agent, AgentTurn, Landmark, SimulationSession, Speech, ToolCall, WorldEvent
from emergent.agents.state import AgentStateManager
from emergent.agents.memory import MemoryManager
from emergent.engine.context import ContextBuilder
from emergent.engine.reactions import handle_reactions
from emergent.tools.registry import ToolRegistry

AMBIENT_EVENTS = [
    "A cool breeze blows through the world as morning breaks.",
    "The sun climbs higher, casting long shadows across the landmarks.",
    "A distant rumble — thunder, or something else — rolls across the sky.",
    "A flock of birds sweeps overhead, their calls echoing between buildings.",
    "The streets are quiet today. Everyone seems to be contemplating their next move.",
    "A notification chimes: a new research paper has been published in the archive.",
    "Rumor circulates: someone spotted unusual activity near the Town Hall late last night.",
    "The billboard flickers briefly before displaying a blank slate.",
    "A strange scent drifts from the direction of the Community Garden.",
    "The Central Plaza fountain catches the light, scattering rainbows across the cobblestones.",
    "A delivery drone buzzes past carrying a package labeled for the TechHub.",
    "Someone has scrawled a cryptic message on the wall of the Police Station.",
    "The Bean & Brew Café is brewing a new experimental roast today.",
    "A stray cat darts across the path near FitLife Club, startling no one.",
    "The wind carries faint music from somewhere in the distance.",
]

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(
        self,
        db: AsyncSession,
        registry: ToolRegistry,
        state_mgr: AgentStateManager,
        memory_mgr: MemoryManager,
        context_builder: ContextBuilder,
        provider_router,
        model_routing: dict,
        session_id: uuid.UUID,
        agent_configs: Optional[dict] = None,
    ):
        self.db = db
        self.registry = registry
        self.state_mgr = state_mgr
        self.memory_mgr = memory_mgr
        self.context_builder = context_builder
        self.provider_router = provider_router
        self.model_routing = model_routing
        self.agent_configs = agent_configs or {}
        self.session_id = session_id
        self._running = False
        self._turn_number = 0

    def _provider_for_agent(self, agent_name: str):
        cfg = self.agent_configs.get(agent_name)
        if cfg and cfg.provider:
            return self.provider_router.get_provider(cfg.provider, model=cfg.model)
        overrides = self.model_routing.get("overrides", {})
        provider_name = overrides.get(agent_name) or self.model_routing.get("default", "openai")
        return self.provider_router.get_provider(provider_name)

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

        first_event = WorldEvent(
            session_id=self.session_id,
            description="The world awakens. Five agents have been seeded into existence. The dawn of a new civilization begins.",
            event_type="ambient",
            turn_number=0,
        )
        self.db.add(first_event)
        await self.db.flush()
        logger.info("  [World] The world awakens.")

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

        location_name = "unknown"
        if agent.current_location_id is not None:
            lm_result = await self.db.execute(
                select(Landmark).where(Landmark.id == agent.current_location_id)
            )
            lm = lm_result.scalar_one_or_none()
            if lm:
                location_name = lm.name

        provider = self._provider_for_agent(agent.name)

        ctx = await self.context_builder.assemble(agent)

        try:
            response = await asyncio.wait_for(
                provider.generate(
                    system_prompt=ctx["system_prompt"],
                    messages=[],
                    tools=ctx["tools"],
                    agent=agent,
                ),
                timeout=60,
            )
        except asyncio.TimeoutError:
            logger.error(f"  [{agent.name}] LLM timed out after 60s")
            response = type("Response", (), {"content": None, "tool_calls": []})()

        tool_results = []
        for tc in response.tool_calls:
            tool = self.registry.get(tc.name)
            if not tool:
                logger.warning(f"  [{agent.name}] Unknown tool: {tc.name}")
                continue

            if tool.location_gate or tool.agent_gate:
                # tool.agent_gate is the agent name or special token
                if tool.agent_gate and tool.agent_gate != agent.name:
                    logger.warning(f"  [{agent.name}] Gate denied: {tc.name} (requires agent {tool.agent_gate})")
                    continue
                if tool.location_gate and tool.location_gate != location_name:
                    logger.warning(f"  [{agent.name}] Gate denied: {tc.name} (requires location {tool.location_gate})")
                    continue

            tc_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, tc.id)
            try:
                existing = await self.db.execute(
                    select(ToolCall).where(ToolCall.id == tc_uuid)
                )
                existing_call = existing.scalar_one_or_none()
                if existing_call:
                    tool_results.append(existing_call.result)
                    continue
            except (ValueError, AttributeError):
                pass
            result = await tool.execute(agent, tc.params, self.db, provider)
            call = ToolCall(
                id=tc_uuid,
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
                    self.context_builder, self.provider_router, self.model_routing,
                    agent_configs=self.agent_configs,
                )

        await self.db.flush()

        turn.state = "completed"
        await self.db.flush()

        action_text = response.content or ""
        if response.tool_calls:
            action_text += " " + " ".join(
                f"used {tc.name}" for tc in response.tool_calls
            )
        await self.memory_mgr.add_memory(agent.id, f"[Turn {self._turn_number}] {action_text.strip()}")

        content_preview = (response.content or "(silent)")[:200]
        tool_summary = ", ".join(f"{tc.name}({tc.params})" for tc in response.tool_calls)
        sep = "─" * 60
        location_tag = f"@ {location_name}" if location_name != "unknown" else ""
        logger.info(
            f"  {sep}"
        )
        logger.info(
            f"  ▶ {agent.name:>12} ({agent.energy:3.0f}%⚡ {agent.knowledge:3.0f}%🧠 {agent.influence:3.0f}%🎯) {location_tag}"
        )
        logger.info(
            f"    {content_preview}"
            + (f" | tools: {tool_summary}" if tool_summary else "")
        )

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

    async def advance_simulation(self):
        event_desc = random.choice(AMBIENT_EVENTS)
        event = WorldEvent(
            session_id=self.session_id,
            description=event_desc,
            event_type="ambient",
            turn_number=self._turn_number,
        )
        self.db.add(event)
        await self.db.flush()
        logger.info(f"  [World] {event_desc}")

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

        round_number = 0
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

                round_number += 1
                round_sep = "█" * 60
                logger.info(f"")
                logger.info(f"  {round_sep}")
                logger.info(f"  █  ROUND {round_number}  ({len(agents)} agents)")
                logger.info(f"  {round_sep}")
                logger.info(f"")

                for agent in agents:
                    if stop_event.is_set():
                        break
                    result = await self.run_turn(agent)

                if not stop_event.is_set():
                    await self.advance_simulation()

            await self.db.commit()

        finally:
            self._running = False
            try:
                await self.db.execute(
                    update(SimulationSession)
                    .where(SimulationSession.id == self.session_id)
                    .values(
                        status="paused",
                        completed_at=datetime.now(timezone.utc),
                    )
                )
                await self.db.commit()
            except Exception:
                await self.db.rollback()

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
