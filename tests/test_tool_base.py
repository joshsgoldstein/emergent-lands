import pytest
from emergent.tools.base import Tool, ToolResult, Parameter


def test_tool_result_success():
    r = ToolResult(success=True, data={"key": "value"})
    assert r.success
    assert r.data == {"key": "value"}
    assert r.error is None


def test_tool_result_failure():
    r = ToolResult(success=False, error="Something went wrong")
    assert not r.success
    assert r.error == "Something went wrong"


def test_tool_is_abstract():
    import inspect
    assert inspect.isabstract(Tool)


def test_tool_has_required_attributes():
    assert hasattr(Tool, "name")
    assert hasattr(Tool, "description")
    assert hasattr(Tool, "execute")


def test_to_tool_definition():
    tool = ConcreteTool()
    td = tool.to_tool_definition()
    assert td.name == "test_tool"
    assert td.parameters["type"] == "object"
    assert "msg" in td.parameters["properties"]


class ConcreteTool(Tool):
    name = "test_tool"
    description = "A test tool"
    parameters = [Parameter(name="msg", type="string", description="A message")]

    async def execute(self, agent, params, db, llm):
        return ToolResult(success=True, data={"echo": params.get("msg")})


@pytest.mark.asyncio
async def test_concrete_tool_executes():
    tool = ConcreteTool()
    result = await tool.execute(None, {"msg": "hello"}, None, None)
    assert result.success
    assert result.data["echo"] == "hello"
