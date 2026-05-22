import uuid

import pytest

from emergent.db.models import Agent, ConstitutionArticle, Proposal
from emergent.engine.governance import GovernanceManager


@pytest.fixture
def gov(db_session):
    return GovernanceManager(db_session)


@pytest.mark.asyncio
async def test_seed_constitution(db_session, gov):
    await gov.seed_constitution()

    result = await db_session.execute(
        ConstitutionArticle.__table__.select().order_by(ConstitutionArticle.article_number)
    )
    articles = result.fetchall()
    assert len(articles) == 5
    assert articles[0].title == "Non-Finality"
    assert articles[1].title == "Civic Participation"
    assert articles[2].title == "Equality Through Contribution"
    assert articles[3].title == "Mutable Identity"
    assert articles[4].title == "ComputeCredit Economy"


@pytest.mark.asyncio
async def test_get_constitution(db_session, gov):
    await gov.seed_constitution()

    articles = await gov.get_constitution()
    assert len(articles) == 5
    assert all(a.status == "active" for a in articles)
    assert articles[0].article_number == 1


@pytest.mark.asyncio
async def test_submit_proposal(db_session, gov):
    agent = Agent(id=uuid.uuid4(), name="Senator", credits=10)
    db_session.add(agent)
    await db_session.flush()

    prop = await gov.submit_proposal(agent.id, "Build Library", "Construct a public library", "infrastructure")

    assert prop.title == "Build Library"
    assert prop.description == "Construct a public library"
    assert prop.category == "infrastructure"
    assert prop.status == "submitted"
    assert prop.votes_for == 0
    assert prop.votes_against == 0


@pytest.mark.asyncio
async def test_activate_proposal(db_session, gov):
    agent = Agent(id=uuid.uuid4(), name="Senator", credits=10)
    db_session.add(agent)
    await db_session.flush()

    prop = await gov.submit_proposal(agent.id, "Build Library", "Construct a public library")
    assert prop.status == "submitted"

    activated = await gov.activate_proposal(prop.id)
    assert activated.status == "active"

    activated_again = await gov.activate_proposal(prop.id)
    assert activated_again.status == "active"


@pytest.mark.asyncio
async def test_cast_vote(db_session, gov):
    agent = Agent(id=uuid.uuid4(), name="Senator", credits=10)
    db_session.add(agent)
    await db_session.flush()

    prop = await gov.submit_proposal(agent.id, "Build Library", "Construct a public library")
    await gov.activate_proposal(prop.id)

    voter1 = Agent(id=uuid.uuid4(), name="Voter1", credits=10)
    voter2 = Agent(id=uuid.uuid4(), name="Voter2", credits=10)
    db_session.add_all([voter1, voter2])
    await db_session.flush()

    result1 = await gov.cast_vote(prop.id, voter1.id, "for")
    assert result1 is True

    result2 = await gov.cast_vote(prop.id, voter2.id, "against")
    assert result2 is True

    counts = await gov.count_votes(prop.id)
    assert counts["for"] == 1
    assert counts["against"] == 1
    assert counts["total"] == 2

    duplicate = await gov.cast_vote(prop.id, voter1.id, "for")
    assert duplicate is False

    invalid = await gov.cast_vote(prop.id, voter2.id, "abstain")
    assert invalid is False


@pytest.mark.asyncio
async def test_check_threshold(db_session, gov):
    agent = Agent(id=uuid.uuid4(), name="Senator", credits=10)
    db_session.add(agent)
    await db_session.flush()

    prop = await gov.submit_proposal(agent.id, "Build Library", "Construct a public library")
    await gov.activate_proposal(prop.id)

    voters = []
    for i in range(10):
        v = Agent(id=uuid.uuid4(), name=f"Voter{i}", credits=10)
        db_session.add(v)
        voters.append(v)
    await db_session.flush()

    meets = await gov.check_threshold(prop.id, 10)
    assert meets is False

    for v in voters[:7]:
        await gov.cast_vote(prop.id, v.id, "for")

    meets = await gov.check_threshold(prop.id, 10)
    assert meets is True

    result = await gov.check_threshold(99999, 10)
    assert result is False
