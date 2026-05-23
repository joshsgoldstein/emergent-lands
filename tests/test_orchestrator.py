import uuid

import pytest
from unittest.mock import AsyncMock

from emergent.engine.orchestrator import Orchestrator
from emergent.agents.state import AgentStateManager
from emergent.agents.memory import MemoryManager
from emergent.engine.context import ContextBuilder
from emergent.tools.registry import ToolRegistry
from emergent.tools.core import register_all_core_tools
from emergent.models.base import LLMResponse, TokenUsage


@pytest.mark.asyncio
async def test_initialize_simulation(db_session):
    registry = ToolRegistry()
    register_all_core_tools(registry)
    sm = AgentStateManager(db_session)
    mm = MemoryManager(db_session)
    cb = ContextBuilder(db_session, registry)
    mock_provider = AsyncMock()
    mock_provider.generate.return_value = LLMResponse(
        content="Hello", tool_calls=[], usage=None, finish_reason="stop"
    )

    sid = uuid.uuid4()
    orch = Orchestrator(db_session, registry, sm, mm, cb, mock_provider, session_id=sid)
    session = await orch.initialize_simulation("config/worlds/mvp.yaml", "test-session")
    assert session.name == "test-session"
    assert session.status == "running"
    assert session.world_path == "config/worlds/mvp.yaml"


@pytest.mark.asyncio
async def test_run_turn_with_mock_provider(db_session):
    registry = ToolRegistry()
    register_all_core_tools(registry)
    sm = AgentStateManager(db_session)
    mm = MemoryManager(db_session)
    cb = ContextBuilder(db_session, registry)

    mock_provider = AsyncMock()
    mock_provider.generate.return_value = LLMResponse(
        content="I'll stay here.",
        tool_calls=[],
        usage=TokenUsage(prompt_tokens=10, completion_tokens=5),
        finish_reason="stop",
    )

    sid = uuid.uuid4()
    orch = Orchestrator(db_session, registry, sm, mm, cb, mock_provider, session_id=sid)

    from sqlalchemy import select
    from emergent.db.models import Landmark
    result = await db_session.execute(select(Landmark))
    landmark = result.scalar_one_or_none()
    if not landmark:
        landmark_obj = Landmark(name="Town Hall", x_coord=100, z_coord=50)
        db_session.add(landmark_obj)
        await db_session.flush()

    agent = await sm.create_agent(name="TurnBot", role="Tester",
                                  personality="", drive="Test", north_star="Test")
    await orch.initialize_simulation("config/worlds/mvp.yaml", "run-test")
    result = await orch.run_turn(agent)
    assert result["agent"] == "TurnBot"
    assert result["response"] == "I'll stay here."


@pytest.mark.asyncio
async def test_recover_no_state(db_session):
    registry = ToolRegistry()
    register_all_core_tools(registry)
    sm = AgentStateManager(db_session)
    mm = MemoryManager(db_session)
    cb = ContextBuilder(db_session, registry)

    sid = uuid.uuid4()
    orch = Orchestrator(db_session, registry, sm, mm, cb, None, session_id=sid)
    state = await orch.recover()
    assert state is None


@pytest.mark.asyncio
async def test_recover_with_interrupted_turns(db_session):
    registry = ToolRegistry()
    register_all_core_tools(registry)
    sm = AgentStateManager(db_session)
    mm = MemoryManager(db_session)
    cb = ContextBuilder(db_session, registry)

    sid = uuid.uuid4()
    orch = Orchestrator(db_session, registry, sm, mm, cb, None, session_id=sid)
    await orch.initialize_simulation("config/worlds/mvp.yaml", "crash-test")

    from sqlalchemy import select
    from emergent.db.models import AgentTurn
    agent = await sm.create_agent(name="CrashBot", role="Tester",
                                  personality="", drive="Test", north_star="Test")

    turn = AgentTurn(session_id=sid, agent_id=agent.id, turn_number=1, state="in_progress")
    db_session.add(turn)
    await db_session.flush()

    state = await orch.recover()
    assert state is not None
    result = await db_session.execute(
        select(AgentTurn).where(AgentTurn.id == turn.id)
    )
    recovered_turn = result.scalar_one()
    assert recovered_turn.state == "interrupted"
