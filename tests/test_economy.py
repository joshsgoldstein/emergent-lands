import uuid

import pytest
from sqlalchemy import select

from emergent.db.models import Agent, CreditTransaction, Pitch
from emergent.engine.economy import CreditManager


@pytest.fixture
def credit_manager(db_session):
    return CreditManager(db_session)


@pytest.mark.asyncio
async def test_transfer_credits(db_session, credit_manager):
    alice = Agent(id=uuid.uuid4(), name="Alice", credits=100)
    bob = Agent(id=uuid.uuid4(), name="Bob", credits=0)
    db_session.add_all([alice, bob])
    await db_session.flush()

    tx = await credit_manager.transfer(alice.id, bob.id, 50, "payment")

    assert tx.amount == 50
    assert tx.from_id == alice.id
    assert tx.to_id == bob.id
    assert tx.reason == "payment"

    alice_bal = await credit_manager.get_balance(alice.id)
    bob_bal = await credit_manager.get_balance(bob.id)
    assert alice_bal == -50
    assert bob_bal == 50


@pytest.mark.asyncio
async def test_get_balance(db_session, credit_manager):
    alice = Agent(id=uuid.uuid4(), name="Alice", credits=100)
    bob = Agent(id=uuid.uuid4(), name="Bob", credits=0)
    db_session.add_all([alice, bob])
    await db_session.flush()

    await credit_manager.transfer(alice.id, bob.id, 30)
    await credit_manager.transfer(alice.id, bob.id, 20)

    bal = await credit_manager.get_balance(bob.id)
    assert bal == 50


@pytest.mark.asyncio
async def test_submit_pitch(db_session, credit_manager):
    agent = Agent(id=uuid.uuid4(), name="Builder", credits=10)
    db_session.add(agent)
    await db_session.flush()

    pitch = await credit_manager.submit_pitch(agent.id, "Build a tower", "http://example.com/tower", 1)

    assert pitch.title == "Build a tower"
    assert pitch.evidence_url == "http://example.com/tower"
    assert pitch.cycle_number == 1
    assert pitch.agent_id == agent.id
    assert pitch.vote_count == 0
    assert pitch.reward is None


@pytest.mark.asyncio
async def test_vote_pitch(db_session, credit_manager):
    agent = Agent(id=uuid.uuid4(), name="Builder", credits=10)
    db_session.add(agent)
    await db_session.flush()

    pitch = await credit_manager.submit_pitch(agent.id, "Build a tower", "http://example.com/tower", 1)

    result = await credit_manager.vote_pitch(pitch.id)
    assert result.vote_count == 1

    result = await credit_manager.vote_pitch(pitch.id)
    assert result.vote_count == 2


@pytest.mark.asyncio
async def test_process_pitch_cycle(db_session, credit_manager):
    agents = []
    for name in ["Alice", "Bob", "Charlie", "Diana"]:
        agent = Agent(id=uuid.uuid4(), name=name, credits=10)
        db_session.add(agent)
        agents.append(agent)
    await db_session.flush()

    pitches = []
    for i, agent in enumerate(agents):
        p = await credit_manager.submit_pitch(agent.id, f"Pitch {i}", f"http://example.com/{i}", 1)
        pitches.append(p)

    await credit_manager.vote_pitch(pitches[0].id)
    await credit_manager.vote_pitch(pitches[0].id)
    await credit_manager.vote_pitch(pitches[0].id)
    await credit_manager.vote_pitch(pitches[1].id)
    await credit_manager.vote_pitch(pitches[1].id)
    await credit_manager.vote_pitch(pitches[2].id)

    await credit_manager.process_pitch_cycle(1)

    result = await db_session.execute(
        select(Pitch).where(Pitch.cycle_number == 1).order_by(Pitch.vote_count.desc())
    )
    updated = list(result.scalars().all())
    assert updated[0].reward == 20
    assert updated[1].reward == 10
    assert updated[2].reward == 10
    assert updated[3].reward is None
