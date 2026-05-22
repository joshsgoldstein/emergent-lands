import pytest
from emergent.tools.base import Tool, ToolResult
from emergent.tools.registry import ToolRegistry


class GoToPlaceTool(Tool):
    name = "go_to_place"
    description = "Move to a landmark"
    parameters = []
    async def execute(self, agent, params, db, llm):
        return ToolResult(success=True)


class SubmitProposalTool(Tool):
    name = "submit_proposal"
    description = "Submit a governance proposal"
    location_gate = "Town Hall"
    parameters = []
    async def execute(self, agent, params, db, llm):
        return ToolResult(success=True)


class ForceDebateTool(Tool):
    name = "force_debate"
    description = "Force a debate"
    agent_gate = "Anchor"
    parameters = []
    async def execute(self, agent, params, db, llm):
        return ToolResult(success=True)


class MockAgent:
    def __init__(self, name, location):
        self.name = name
        self.current_location = location


def test_register_and_get():
    registry = ToolRegistry()
    tool = GoToPlaceTool()
    registry.register(tool)
    assert registry.get("go_to_place") is tool


def test_duplicate_name_raises():
    registry = ToolRegistry()
    registry.register(GoToPlaceTool())
    with pytest.raises(ValueError, match="already registered"):
        registry.register(GoToPlaceTool())


def test_get_available_core_tools():
    registry = ToolRegistry()
    registry.register(GoToPlaceTool())
    agent = MockAgent(name="Flora", location="Town Hall")
    available = registry.get_available(agent)
    assert len(available) == 1
    assert available[0].name == "go_to_place"


def test_get_available_filters_by_location():
    registry = ToolRegistry()
    registry.register(GoToPlaceTool())
    registry.register(SubmitProposalTool())
    agent_at_town_hall = MockAgent(name="Flora", location="Town Hall")
    agent_at_library = MockAgent(name="Flora", location="Library")
    assert len(registry.get_available(agent_at_town_hall)) == 2
    assert len(registry.get_available(agent_at_library)) == 1


def test_get_available_filters_by_agent():
    registry = ToolRegistry()
    registry.register(GoToPlaceTool())
    registry.register(ForceDebateTool())
    anchor = MockAgent(name="Anchor", location="Town Hall")
    flora = MockAgent(name="Flora", location="Town Hall")
    assert len(registry.get_available(anchor)) == 2
    assert len(registry.get_available(flora)) == 1


def test_get_available_as_tool_definitions():
    registry = ToolRegistry()
    registry.register(GoToPlaceTool())
    agent = MockAgent(name="Flora", location="Town Hall")
    defs = registry.get_available_as_definitions(agent)
    assert len(defs) == 1
    assert defs[0].name == "go_to_place"
    assert defs[0].parameters["type"] == "object"


def test_len():
    registry = ToolRegistry()
    assert len(registry) == 0
    registry.register(GoToPlaceTool())
    assert len(registry) == 1
