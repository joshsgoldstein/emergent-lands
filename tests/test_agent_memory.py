import uuid
import pytest
from sqlalchemy import select
from emergent.agents.memory import MemoryManager
from emergent.agents.state import AgentStateManager
from emergent.db.models import Agent, SoulEntry


@pytest.fixture
def agent_ids(db_session):
    mgr = AgentStateManager(db_session)
    return mgr


@pytest.mark.asyncio
async def test_add_and_get_memory(db_session):
    mgr = MemoryManager(db_session)
    am = AgentStateManager(db_session)
    agent = await am.create_agent(name="MemoryTest", role="Tester")
    mem = await mgr.add_memory(agent.id, "Saw something interesting")
    assert mem.content == "Saw something interesting"
    assert mem.type == "long_term"
    memories = await mgr.get_recent_memories(agent.id)
    assert len(memories) == 1


@pytest.mark.asyncio
async def test_write_diary(db_session):
    mgr = MemoryManager(db_session)
    am = AgentStateManager(db_session)
    agent = await am.create_agent(name="DiaryTest", role="Tester")
    entry = await mgr.write_diary(agent.id, {"text": "Good day"}, "happy")
    assert entry.mood == "happy"
    assert entry.content["text"] == "Good day"
    diary = await mgr.get_diary(agent.id)
    assert len(diary) == 1


@pytest.mark.asyncio
async def test_set_relationship(db_session):
    mgr = MemoryManager(db_session)
    am = AgentStateManager(db_session)
    a1 = await am.create_agent(name="RelA", role="A")
    a2 = await am.create_agent(name="RelB", role="B")
    rel = await mgr.set_relationship(a1.id, a2.id, "ally", trust=0.8)
    assert rel.relationship_type == "ally"
    assert rel.trust == 0.8
    rel2 = await mgr.set_relationship(a1.id, a2.id, "ally", trust=0.9)
    assert rel2.interaction_count == 2


@pytest.mark.asyncio
async def test_get_relationship_summary_empty(db_session):
    mgr = MemoryManager(db_session)
    am = AgentStateManager(db_session)
    agent = await am.create_agent(name="Lonely", role="T")
    summary = await mgr.get_relationship_summary(agent.id)
    assert "No established relationships" in summary


@pytest.mark.asyncio
async def test_get_soul_entries(db_session):
    mgr = MemoryManager(db_session)
    am = AgentStateManager(db_session)
    agent = await am.create_agent(name="SoulTest", role="T")
    for i in range(3):
        db_session.add(SoulEntry(agent_id=agent.id, content=f"Soul {i}"))
    await db_session.flush()
    entries = await mgr.get_soul_entries(agent.id)
    assert len(entries) == 3
