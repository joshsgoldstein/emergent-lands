import pytest
from sqlalchemy import inspect

from emergent.db.base import Base
from emergent.db import models  # noqa: F401


class TestModels:
    def test_all_tables_have_names(self):
        mapper_classes = Base.registry.mappers
        for mapper in mapper_classes:
            table = mapper.tables[0]
            assert table.name
            assert len(table.columns) > 0

    def test_required_tables_exist(self):
        expected = {
            "simulation_state", "agents", "agent_turns", "tool_calls",
            "memories", "soul_entries", "diary_entries", "relationships",
            "messages", "speech", "landmarks", "proposals", "votes",
            "constitution_articles", "credit_transactions", "pitches",
            "blogs", "community_events",
        }
        tables = set(Base.metadata.tables.keys())
        missing = expected - tables
        assert not missing, f"Missing tables: {missing}"

    @pytest.mark.asyncio
    async def test_schema_creates_in_postgres(self, test_db_engine):
        async with test_db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            tables = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names()
            )
        for name in ["agents", "landmarks", "memories"]:
            assert name in tables
