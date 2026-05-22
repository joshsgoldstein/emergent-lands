import pytest

from emergent.agents.memory import MemoryManager
from emergent.agents.state import AgentStateManager
from emergent.db.models import Landmark, SoulEntry
from emergent.engine.context import ContextBuilder
from emergent.tools.base import Tool, ToolResult
from emergent.tools.registry import ToolRegistry


class DummyTool(Tool):
    name = "say"
    description = "Say something"
    parameters = []
    async def execute(self, agent, params, db, llm):
        return ToolResult(success=True)


@pytest.mark.asyncio
async def test_context_includes_all_sections(db_session):
    db_session.add(Landmark(name="Garden", x_coord=0.0, z_coord=0.0))
    await db_session.flush()

    am = AgentStateManager(db_session)
    agent = await am.create_agent(
        name="Flora",
        role="Botanist",
        personality="Curious",
        drive="Discover plants",
        north_star="Catalog all species",
        home="Garden",
    )
    await am.seed_soul_entries(agent.id, ["I love plants", "Nature is life"])
    mm = MemoryManager(db_session)
    await mm.add_memory(agent.id, "Found a rare flower")

    registry = ToolRegistry()
    registry.register(DummyTool())
    builder = ContextBuilder(db_session, registry)
    ctx = await builder.assemble(agent)

    assert "system_prompt" in ctx
    assert "tools" in ctx
    prompt = ctx["system_prompt"]
    assert "Flora" in prompt
    assert "Botanist" in prompt
    assert "I love plants" in prompt
    assert "Nature is life" in prompt
    assert "Found a rare flower" in prompt
    assert "Garden" in prompt
    assert len(ctx["tools"]) == 1
    assert ctx["tools"][0].name == "say"


@pytest.mark.asyncio
async def test_context_with_no_memories_or_relationships(db_session):
    am = AgentStateManager(db_session)
    agent = await am.create_agent(name="Lonely", role="Hermit")

    registry = ToolRegistry()
    builder = ContextBuilder(db_session, registry)
    ctx = await builder.assemble(agent)

    prompt = ctx["system_prompt"]
    assert "Lonely" in prompt
    assert "Hermit" in prompt
    assert "No soul entries yet" in prompt
    assert "No memories yet" in prompt
    assert "No established relationships" in prompt
    assert ctx["tools"] == []
