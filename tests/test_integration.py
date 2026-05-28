"""Integration smoke test: validates Week 1 core systems work together."""
import os
import pytest

from emergent.db.connection import DatabaseManager, get_database_url
from emergent.db.base import Base
from emergent.tools.registry import ToolRegistry
from emergent.tools.core import register_all_core_tools
from emergent.models.router import ProviderRouter, ProviderConfig
from emergent.world.config import load_world_config


@pytest.mark.asyncio
async def test_db_init_and_tool_registry():
    mgr = DatabaseManager(get_database_url())
    await mgr.initialize()
    async with mgr.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    registry = ToolRegistry()
    register_all_core_tools(registry)
    assert len(registry) > 0

    await mgr.close()


@pytest.mark.asyncio
async def test_provider_router_opens():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set — skipping live LLM test")

    configs = {
        "openai": ProviderConfig(
            provider="openai",
            model="gpt-5-mini",
            api_key=api_key,
        ),
    }
    router = ProviderRouter(configs)
    provider = router.get_provider("default")
    assert provider.name == "openai"


def test_full_tool_definition_round_trip():
    from emergent.tools.base import Tool, ToolResult, Parameter

    registry = ToolRegistry()
    register_all_core_tools(registry)

    class MockAgent:
        name = "TestAgent"
        current_location = "Town Hall"

    agent = MockAgent()
    definitions = registry.get_available_as_definitions(agent)
    assert len(definitions) > 0
    for d in definitions:
        assert d.name
        assert d.description
        assert d.parameters["type"] == "object"


def test_world_config_round_trip():
    config = load_world_config("config/worlds/mvp.yaml")
    assert config.name == "MVP World"
    assert len(config.agents) == 5
    assert "Town Hall" in config.landmarks
    assert config.providers["openai"]["model"] == "deepseek/deepseek-v4-flash"


def test_load_world_and_create_registry():
    config = load_world_config("config/worlds/mvp.yaml")
    from emergent.tools.core import GoToPlaceTool

    registry = ToolRegistry()
    registry.register(GoToPlaceTool())

    class MockAgent:
        name = "Anchor"
        current_location = "Town Hall"

    agent = MockAgent()
    tools = registry.get_available(agent)
    assert len(tools) >= 1
