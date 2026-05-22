import uuid

import pytest
from sqlalchemy import select

from emergent.agents.state import AgentStateManager
from emergent.db.models import SoulEntry


@pytest.mark.asyncio
async def test_create_agent(db_session):
    mgr = AgentStateManager(db_session)
    agent = await mgr.create_agent(name="TestAgent", role="Tester")
    assert agent.name == "TestAgent"
    assert agent.role == "Tester"
    assert agent.energy == 100.0
    assert agent.credits == 10


@pytest.mark.asyncio
async def test_get_agent_by_name(db_session):
    mgr = AgentStateManager(db_session)
    await mgr.create_agent(name="TestAgent", role="Tester")
    agent = await mgr.get_agent_by_name("TestAgent")
    assert agent is not None
    assert agent.name == "TestAgent"


@pytest.mark.asyncio
async def test_living_agents(db_session):
    mgr = AgentStateManager(db_session)
    await mgr.create_agent(name="Alice", role="A")
    bob = await mgr.create_agent(name="Bob", role="B")
    bob.status = "dead"
    await db_session.flush()
    living = await mgr.get_living_agents()
    names = [a.name for a in living]
    assert "Alice" in names
    assert "Bob" not in names


@pytest.mark.asyncio
async def test_apply_needs_decay(db_session):
    mgr = AgentStateManager(db_session)
    agent = await mgr.create_agent(name="DecayTest", role="T")
    await mgr.apply_needs_decay(agent, hours_passed=1.0)
    assert agent.energy < 100.0
    assert agent.energy == pytest.approx(96.7, abs=0.1)


@pytest.mark.asyncio
async def test_death_at_zero_energy(db_session):
    mgr = AgentStateManager(db_session)
    agent = await mgr.create_agent(name="Mortal", role="T")
    agent.energy = 5.0
    await db_session.flush()
    await mgr.apply_needs_decay(agent, hours_passed=2.0)
    assert agent.status == "dead"


@pytest.mark.asyncio
async def test_seed_soul_entries(db_session):
    mgr = AgentStateManager(db_session)
    agent = await mgr.create_agent(name="SoulTest", role="T")
    await mgr.seed_soul_entries(agent.id, ["Belief 1", "Belief 2"])
    result = await db_session.execute(
        select(SoulEntry).where(SoulEntry.agent_id == agent.id)
    )
    entries = result.scalars().all()
    assert len(entries) == 2
