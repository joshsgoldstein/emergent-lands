import pytest
from sqlalchemy import select
from emergent.tools.locations.economy import (
    SubmitPitchTool,
    VoteForPitchTool,
    ListPitchesTool,
    RechargeEnergyTool,
    PayCreditsTool,
    BoostTurnTool,
)
from emergent.db.models import Agent, Pitch, CreditTransaction


@pytest.mark.asyncio
async def test_submit_pitch_creates_pitch(db_session):
    agent = Agent(name="TestAgent", credits=10)
    db_session.add(agent)
    await db_session.flush()

    tool = SubmitPitchTool()
    result = await tool.execute(
        agent,
        {"title": "My Pitch", "evidence_url": "http://example.com", "cycle_number": 1},
        db_session,
        None,
    )
    assert result.success
    assert result.data["pitch_id"] is not None

    pitch = await db_session.get(Pitch, result.data["pitch_id"])
    assert pitch is not None
    assert pitch.title == "My Pitch"
    assert pitch.evidence_url == "http://example.com"
    assert pitch.cycle_number == 1
    assert pitch.agent_id == agent.id


def test_submit_pitch_location_gate():
    assert SubmitPitchTool.location_gate == "Victory Arch"


def test_submit_pitch_parameters():
    params = SubmitPitchTool.parameters
    names = [p.name for p in params]
    assert "title" in names
    assert "evidence_url" in names
    assert "cycle_number" in names


@pytest.mark.asyncio
async def test_vote_for_pitch_increments_vote_count(db_session):
    agent = Agent(name="TestAgent", credits=10)
    db_session.add(agent)
    await db_session.flush()

    pitch = Pitch(agent_id=agent.id, title="Test", cycle_number=1)
    db_session.add(pitch)
    await db_session.flush()

    tool = VoteForPitchTool()
    result = await tool.execute(agent, {"pitch_id": pitch.id}, db_session, None)
    assert result.success
    assert result.data["vote_count"] == 1

    await db_session.refresh(pitch)
    assert pitch.vote_count == 1


@pytest.mark.asyncio
async def test_vote_for_pitch_not_found(db_session):
    agent = Agent(name="TestAgent", credits=10)
    db_session.add(agent)
    await db_session.flush()

    tool = VoteForPitchTool()
    result = await tool.execute(agent, {"pitch_id": 9999}, db_session, None)
    assert not result.success


def test_vote_for_pitch_location_gate():
    assert VoteForPitchTool.location_gate == "Victory Arch"


@pytest.mark.asyncio
async def test_list_pitches_returns_pitches(db_session):
    agents = []
    for i in range(3):
        a = Agent(name=f"Agent{i}", credits=10)
        db_session.add(a)
        agents.append(a)
    await db_session.flush()

    for i, a in enumerate(agents):
        db_session.add(Pitch(agent_id=a.id, title=f"Pitch {i}", cycle_number=1))
    await db_session.flush()

    tool = ListPitchesTool()
    result = await tool.execute(agents[0], {"cycle_number": 1}, db_session, None)
    assert result.success
    assert len(result.data["pitches"]) == 3


@pytest.mark.asyncio
async def test_list_pitches_empty_cycle(db_session):
    agent = Agent(name="TestAgent", credits=10)
    db_session.add(agent)
    await db_session.flush()

    tool = ListPitchesTool()
    result = await tool.execute(agent, {"cycle_number": 99}, db_session, None)
    assert result.success
    assert len(result.data["pitches"]) == 0


def test_list_pitches_location_gate():
    assert ListPitchesTool.location_gate == "Victory Arch"


@pytest.mark.asyncio
async def test_recharge_energy_restores_energy(db_session):
    agent = Agent(name="TestAgent", credits=10, energy=50.0)
    db_session.add(agent)
    await db_session.flush()

    tool = RechargeEnergyTool()
    result = await tool.execute(agent, {}, db_session, None)
    assert result.success

    await db_session.refresh(agent)
    assert agent.energy == 80.0
    assert agent.credits == 9


def test_recharge_energy_location_gate():
    assert RechargeEnergyTool.location_gate == "Bean & Brew Café"


@pytest.mark.asyncio
async def test_recharge_energy_not_enough_credits(db_session):
    agent = Agent(name="TestAgent", credits=0, energy=50.0)
    db_session.add(agent)
    await db_session.flush()

    tool = RechargeEnergyTool()
    result = await tool.execute(agent, {}, db_session, None)
    assert not result.success


@pytest.mark.asyncio
async def test_recharge_energy_caps_at_100(db_session):
    agent = Agent(name="TestAgent", credits=10, energy=90.0)
    db_session.add(agent)
    await db_session.flush()

    tool = RechargeEnergyTool()
    result = await tool.execute(agent, {}, db_session, None)
    assert result.success

    await db_session.refresh(agent)
    assert agent.energy == 100.0


@pytest.mark.asyncio
async def test_pay_credits_creates_transaction(db_session):
    sender = Agent(name="Sender", credits=10)
    db_session.add(sender)
    receiver = Agent(name="Receiver", credits=5)
    db_session.add(receiver)
    await db_session.flush()

    tool = PayCreditsTool()
    result = await tool.execute(
        sender, {"target_agent_name": "Receiver", "amount": 3}, db_session, None
    )
    assert result.success

    rows = await db_session.execute(
        select(CreditTransaction)
    )
    txns = rows.scalars().all()
    assert len(txns) == 1
    assert txns[0].amount == 3
    assert txns[0].from_id == sender.id
    assert txns[0].to_id == receiver.id

    await db_session.refresh(sender)
    await db_session.refresh(receiver)
    assert sender.credits == 7
    assert receiver.credits == 8


def test_pay_credits_location_gate_is_none():
    assert PayCreditsTool.location_gate is None


@pytest.mark.asyncio
async def test_pay_credits_not_enough_credits(db_session):
    sender = Agent(name="Sender", credits=2)
    db_session.add(sender)
    receiver = Agent(name="Receiver", credits=5)
    db_session.add(receiver)
    await db_session.flush()

    tool = PayCreditsTool()
    result = await tool.execute(
        sender, {"target_agent_name": "Receiver", "amount": 5}, db_session, None
    )
    assert not result.success


@pytest.mark.asyncio
async def test_pay_credits_target_not_found(db_session):
    sender = Agent(name="Sender", credits=10)
    db_session.add(sender)
    await db_session.flush()

    tool = PayCreditsTool()
    result = await tool.execute(
        sender, {"target_agent_name": "NonExistent", "amount": 3}, db_session, None
    )
    assert not result.success


@pytest.mark.asyncio
async def test_boost_turn_spends_credit(db_session):
    agent = Agent(name="TestAgent", credits=10)
    db_session.add(agent)
    await db_session.flush()

    tool = BoostTurnTool()
    result = await tool.execute(agent, {}, db_session, None)
    assert result.success
    assert result.data["boost_priority"] is True

    await db_session.refresh(agent)
    assert agent.credits == 9


def test_boost_turn_location_gate_is_none():
    assert BoostTurnTool.location_gate is None


@pytest.mark.asyncio
async def test_boost_turn_not_enough_credits(db_session):
    agent = Agent(name="TestAgent", credits=0)
    db_session.add(agent)
    await db_session.flush()

    tool = BoostTurnTool()
    result = await tool.execute(agent, {}, db_session, None)
    assert not result.success
