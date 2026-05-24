import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy import select

from emergent.agents.state import AgentStateManager
from emergent.agents.memory import MemoryManager
from emergent.engine.context import ContextBuilder
from emergent.engine.reactions import handle_reactions
from emergent.tools.registry import ToolRegistry
from emergent.tools.core import register_all_core_tools
from emergent.models.base import LLMResponse, ToolCall, TokenUsage


MODEL_ROUTING = {"default": "openai", "overrides": {}}


def _mock_router(provider):
    router = MagicMock()
    router.get_provider.return_value = provider
    return router


@pytest.mark.asyncio
async def test_handle_reactions_no_nearby(db_session):
    registry = ToolRegistry()
    register_all_core_tools(registry)
    sm = AgentStateManager(db_session)
    mm = MemoryManager(db_session)
    cb = ContextBuilder(db_session, registry)
    mock_provider = AsyncMock()

    from emergent.db.models import Landmark
    landmark = Landmark(name="Quiet Corner", x_coord=0, z_coord=0)
    db_session.add(landmark)
    await db_session.flush()

    agent = await sm.create_agent(name="LonelyBot", role="Tester")
    agent.current_location_id = landmark.id
    await db_session.flush()

    await handle_reactions(agent, "Hello?", db_session, registry, sm, mm, cb, _mock_router(mock_provider), MODEL_ROUTING)
    mock_provider.generate.assert_not_called()


@pytest.mark.asyncio
async def test_handle_reactions_with_listeners(db_session):
    registry = ToolRegistry()
    register_all_core_tools(registry)
    sm = AgentStateManager(db_session)
    mm = MemoryManager(db_session)
    cb = ContextBuilder(db_session, registry)

    from emergent.db.models import Landmark
    landmark = Landmark(name="Plaza", x_coord=10, z_coord=10)
    db_session.add(landmark)
    await db_session.flush()

    speaker = await sm.create_agent(name="Speaker", role="Tester")
    speaker.current_location_id = landmark.id

    listener = await sm.create_agent(name="Listener", role="Tester")
    listener.current_location_id = landmark.id

    await db_session.flush()

    mock_provider = AsyncMock()
    mock_provider.generate.return_value = LLMResponse(
        content="I hear you!",
        tool_calls=[],
        usage=TokenUsage(prompt_tokens=10, completion_tokens=5),
        finish_reason="stop",
    )

    await handle_reactions(speaker, "Hi!", db_session, registry, sm, mm, cb, _mock_router(mock_provider), MODEL_ROUTING)
    mock_provider.generate.assert_called_once()


@pytest.mark.asyncio
async def test_max_listeners(db_session):
    registry = ToolRegistry()
    register_all_core_tools(registry)
    sm = AgentStateManager(db_session)
    mm = MemoryManager(db_session)
    cb = ContextBuilder(db_session, registry)

    from emergent.db.models import Landmark
    landmark = Landmark(name="Busy Square", x_coord=20, z_coord=20)
    db_session.add(landmark)
    await db_session.flush()

    speaker = await sm.create_agent(name="Speaker", role="Tester")
    speaker.current_location_id = landmark.id

    for i in range(6):
        a = await sm.create_agent(name=f"Listener{i}", role="Tester")
        a.current_location_id = landmark.id

    await db_session.flush()

    mock_provider = AsyncMock()
    mock_provider.generate.return_value = LLMResponse(
        content="...",
        tool_calls=[],
        usage=TokenUsage(prompt_tokens=5, completion_tokens=2),
        finish_reason="stop",
    )

    await handle_reactions(speaker, "Everyone!", db_session, registry, sm, mm, cb, _mock_router(mock_provider), MODEL_ROUTING)
    assert mock_provider.generate.call_count <= 4


@pytest.mark.asyncio
async def test_reaction_creates_speech(db_session):
    registry = ToolRegistry()
    register_all_core_tools(registry)
    sm = AgentStateManager(db_session)
    mm = MemoryManager(db_session)
    cb = ContextBuilder(db_session, registry)

    from emergent.db.models import Landmark, Speech
    landmark = Landmark(name="Debate Hall", x_coord=30, z_coord=30)
    db_session.add(landmark)
    await db_session.flush()

    speaker = await sm.create_agent(name="Speaker", role="Tester")
    speaker.current_location_id = landmark.id

    listener = await sm.create_agent(name="Responder", role="Tester")
    listener.current_location_id = landmark.id

    await db_session.flush()

    mock_provider = AsyncMock()
    mock_provider.generate.side_effect = [
        LLMResponse(
            content="I reply!",
            tool_calls=[
                ToolCall(
                    id="mock-1",
                    name="say_to_agent",
                    params={"agent_name": "Speaker", "message": "I agree!"},
                ),
            ],
            usage=TokenUsage(prompt_tokens=10, completion_tokens=5),
            finish_reason="tool_calls",
        ),
        LLMResponse(
            content="...",
            tool_calls=[],
            usage=TokenUsage(prompt_tokens=3, completion_tokens=1),
            finish_reason="stop",
        ),
    ]

    await handle_reactions(speaker, "Let's debate", db_session, registry, sm, mm, cb, _mock_router(mock_provider), MODEL_ROUTING)

    result = await db_session.execute(
        select(Speech).where(Speech.agent_id == listener.id)
    )
    speech_records = result.scalars().all()
    assert len(speech_records) >= 1
    assert speech_records[0].message == "I agree!"
