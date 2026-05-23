import pytest
from emergent.tools.registry import ToolRegistry
from emergent.tools.core import (
    GoToPlaceTool,
    SayToAgentTool,
    AddToMemoryTool,
    WriteDiaryTool,
    ShowEmoticonTool,
    CheckWeatherTool,
    ReadMessagesTool,
    ThinkAloudTool,
    IdleTool,
    IgnoreTool,
    register_all_core_tools,
)


def test_core_tools_register():
    registry = ToolRegistry()
    register_all_core_tools(registry)
    assert len(registry) == 11, f"Expected 11 core tools, got {len(registry)}"


@pytest.mark.asyncio
async def test_go_to_place_executes(db_session):
    from emergent.db.models import Agent, Landmark
    landmark = Landmark(name="Town Hall", description="Governance hub", x_coord=100, z_coord=50)
    db_session.add(landmark)
    agent = Agent(name="Anchor", current_location_id=None)
    db_session.add(agent)
    await db_session.flush()
    tool = GoToPlaceTool()
    result = await tool.execute(agent, {"place": "Town Hall", "reason": "debate"}, db_session, None)
    assert result.success
    assert result.data["place"] == "Town Hall"
    assert agent.current_location_id == landmark.id


@pytest.mark.asyncio
async def test_say_to_agent_executes():
    tool = SayToAgentTool()
    result = await tool.execute(None, {"agent_name": "Flora", "message": "Hello!"}, None, None)
    assert result.success


@pytest.mark.asyncio
async def test_add_to_memory_executes():
    tool = AddToMemoryTool()
    result = await tool.execute(None, {"content": "The café is crowded today"}, None, None)
    assert result.success


@pytest.mark.asyncio
async def test_idle_provides_observation():
    tool = IdleTool()
    result = await tool.execute(None, {"reason": "Thinking..."}, None, None)
    assert result.success
    assert result.observation is not None


@pytest.mark.asyncio
async def test_ignore_executes():
    tool = IgnoreTool()
    result = await tool.execute(None, {}, None, None)
    assert result.success
    assert "ignore" in result.observation.lower()


@pytest.mark.asyncio
async def test_check_weather_returns_data():
    tool = CheckWeatherTool()
    result = await tool.execute(None, {}, None, None)
    assert result.success
    assert "weather" in result.data


def test_register_all_core_tools():
    registry = ToolRegistry()
    register_all_core_tools(registry)
    assert len(registry) == 11
    assert registry.get("go_to_place") is not None
    assert registry.get("idle") is not None
    assert registry.get("say_to_agent") is not None
