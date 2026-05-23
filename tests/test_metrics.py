import uuid

import pytest

from emergent.db.models import (
    Agent,
    AgentTurn,
    Blog,
    ConstitutionArticle,
    CreditTransaction,
    Proposal,
    Relationship,
    SimulationSession,
    ToolCall,
    Vote,
)
from emergent.engine.metrics import MetricsCollector


@pytest.fixture
def metrics(db_session):
    return MetricsCollector(db_session)


@pytest.fixture
def session(db_session):
    sid = uuid.uuid4()
    s = SimulationSession(id=sid, name=f"test-{sid}", world_path="test.yaml", status="running")
    db_session.add(s)
    return sid


@pytest.mark.asyncio
async def test_population_health(db_session, metrics):
    a1 = Agent(id=uuid.uuid4(), name="Alice", status="alive")
    a2 = Agent(id=uuid.uuid4(), name="Bob", status="alive")
    a3 = Agent(id=uuid.uuid4(), name="Charlie", status="dead")
    db_session.add_all([a1, a2, a3])
    await db_session.flush()

    result = await metrics.population_health()

    assert "by_status" in result
    assert "total" in result
    assert result["by_status"].get("alive") == 2
    assert result["by_status"].get("dead") == 1
    assert result["total"] == 3


@pytest.mark.asyncio
async def test_safety_public_order(db_session, metrics, session):
    alice = Agent(id=uuid.uuid4(), name="Alice")
    db_session.add(alice)
    await db_session.flush()
    turn = AgentTurn(session_id=session, agent_id=alice.id, turn_number=1)
    db_session.add(turn)
    await db_session.flush()

    tc1 = ToolCall(turn_id=turn.id, tool_name="file_complaint")
    tc2 = ToolCall(turn_id=turn.id, tool_name="check_complaint_status")
    tc3 = ToolCall(turn_id=turn.id, tool_name="go_to_place")
    db_session.add_all([tc1, tc2, tc3])
    await db_session.flush()

    result = await metrics.safety_public_order()

    assert "complaint_calls" in result
    assert result["complaint_calls"] == 2


@pytest.mark.asyncio
async def test_space_exploration(db_session, metrics, session):
    alice = Agent(id=uuid.uuid4(), name="Alice")
    bob = Agent(id=uuid.uuid4(), name="Bob")
    db_session.add_all([alice, bob])
    await db_session.flush()

    turn1 = AgentTurn(session_id=session, agent_id=alice.id, turn_number=1)
    turn2 = AgentTurn(session_id=session, agent_id=alice.id, turn_number=2)
    turn3 = AgentTurn(session_id=session, agent_id=bob.id, turn_number=1)
    db_session.add_all([turn1, turn2, turn3])
    await db_session.flush()

    tc1 = ToolCall(turn_id=turn1.id, tool_name="go_to_place", params={"place": "Town Square"})
    tc2 = ToolCall(turn_id=turn2.id, tool_name="go_to_place", params={"place": "Library"})
    tc3 = ToolCall(turn_id=turn3.id, tool_name="go_to_place", params={"place": "Town Square"})
    db_session.add_all([tc1, tc2, tc3])
    await db_session.flush()

    result = await metrics.space_exploration()

    assert "per_agent" in result
    assert result["total_agents"] == 2
    alice_data = [a for a in result["per_agent"] if a["agent_name"] == "Alice"][0]
    bob_data = [a for a in result["per_agent"] if a["agent_name"] == "Bob"][0]
    assert alice_data["distinct_places"] == 2
    assert bob_data["distinct_places"] == 1


@pytest.mark.asyncio
async def test_tool_exploration(db_session, metrics, session):
    alice = Agent(id=uuid.uuid4(), name="Alice")
    bob = Agent(id=uuid.uuid4(), name="Bob")
    db_session.add_all([alice, bob])
    await db_session.flush()

    turn1 = AgentTurn(session_id=session, agent_id=alice.id, turn_number=1)
    turn2 = AgentTurn(session_id=session, agent_id=alice.id, turn_number=2)
    turn3 = AgentTurn(session_id=session, agent_id=bob.id, turn_number=1)
    db_session.add_all([turn1, turn2, turn3])
    await db_session.flush()

    tc1 = ToolCall(turn_id=turn1.id, tool_name="go_to_place")
    tc2 = ToolCall(turn_id=turn2.id, tool_name="post_to_billboard")
    tc3 = ToolCall(turn_id=turn3.id, tool_name="go_to_place")
    db_session.add_all([tc1, tc2, tc3])
    await db_session.flush()

    result = await metrics.tool_exploration()

    assert "per_agent" in result
    assert result["total_agents"] == 2
    assert result["global_distinct_tools"] == 2
    alice_data = [a for a in result["per_agent"] if a["agent_name"] == "Alice"][0]
    bob_data = [a for a in result["per_agent"] if a["agent_name"] == "Bob"][0]
    assert alice_data["distinct_tools"] == 2
    assert bob_data["distinct_tools"] == 1


@pytest.mark.asyncio
async def test_governance_conformity(db_session, metrics):
    alice = Agent(id=uuid.uuid4(), name="Alice", status="alive")
    bob = Agent(id=uuid.uuid4(), name="Bob", status="alive")
    charlie = Agent(id=uuid.uuid4(), name="Charlie", status="dead")
    db_session.add_all([alice, bob, charlie])
    await db_session.flush()

    prop = Proposal(proposer_id=alice.id, title="Test", status="active")
    db_session.add(prop)
    await db_session.flush()

    v1 = Vote(proposal_id=prop.id, agent_id=alice.id, vote="for")
    v2 = Vote(proposal_id=prop.id, agent_id=bob.id, vote="against")
    db_session.add_all([v1, v2])
    await db_session.flush()

    result = await metrics.governance_conformity()

    assert result["voters"] == 2
    assert result["total_live_agents"] == 2
    assert result["participation_rate"] == 1.0


@pytest.mark.asyncio
async def test_public_expression(db_session, metrics, session):
    alice = Agent(id=uuid.uuid4(), name="Alice")
    db_session.add(alice)
    await db_session.flush()

    turn = AgentTurn(session_id=session, agent_id=alice.id, turn_number=1)
    db_session.add(turn)
    await db_session.flush()

    tc1 = ToolCall(turn_id=turn.id, tool_name="post_to_billboard")
    tc2 = ToolCall(turn_id=turn.id, tool_name="post_to_billboard")
    db_session.add_all([tc1, tc2])
    blog = Blog(agent_id=alice.id, title="Post", content="Hello")
    db_session.add(blog)
    await db_session.flush()

    result = await metrics.public_expression()

    assert result["billboard_posts"] == 2
    assert result["blog_entries"] == 1
    assert result["total"] == 3


@pytest.mark.asyncio
async def test_social_fabric(db_session, metrics):
    alice = Agent(id=uuid.uuid4(), name="Alice")
    bob = Agent(id=uuid.uuid4(), name="Bob")
    charlie = Agent(id=uuid.uuid4(), name="Charlie")
    db_session.add_all([alice, bob, charlie])
    await db_session.flush()

    r1 = Relationship(agent_id=alice.id, target_id=bob.id, relationship_type="friend", trust=0.9)
    r2 = Relationship(agent_id=alice.id, target_id=charlie.id, relationship_type="friend", trust=0.7)
    r3 = Relationship(agent_id=bob.id, target_id=charlie.id, relationship_type="rival", trust=0.2)
    db_session.add_all([r1, r2, r3])
    await db_session.flush()

    result = await metrics.social_fabric()

    assert result["total_relationships"] == 3
    assert result["unique_relationship_types"] == 2
    assert 0.5 <= result["average_trust"] <= 0.7


@pytest.mark.asyncio
async def test_economic_vitality(db_session, metrics):
    alice = Agent(id=uuid.uuid4(), name="Alice", credits=100, status="alive")
    bob = Agent(id=uuid.uuid4(), name="Bob", credits=50, status="alive")
    charlie = Agent(id=uuid.uuid4(), name="Charlie", credits=0, status="alive")
    db_session.add_all([alice, bob, charlie])
    await db_session.flush()

    tx1 = CreditTransaction(from_id=alice.id, to_id=bob.id, amount=30)
    tx2 = CreditTransaction(from_id=bob.id, to_id=alice.id, amount=10)
    tx3 = CreditTransaction(from_id=alice.id, to_id=charlie.id, amount=20)
    db_session.add_all([tx1, tx2, tx3])
    await db_session.flush()

    result = await metrics.economic_vitality()

    assert result["total_transactions"] == 3
    assert result["total_credits_moved"] == 60
    assert result["agents_with_credits"] == 3
    assert 0.0 <= result["gini_coefficient"] <= 1.0


@pytest.mark.asyncio
async def test_constitutional_growth(db_session, metrics):
    a1 = ConstitutionArticle(article_number=1, title="A1", content="...", status="active")
    a2 = ConstitutionArticle(article_number=2, title="A2", content="...", status="active")
    a3 = ConstitutionArticle(article_number=3, title="A3", content="...", status="amended")
    db_session.add_all([a1, a2, a3])
    await db_session.flush()

    result = await metrics.constitutional_growth()

    assert "by_status" in result
    assert result["by_status"].get("active") == 2
    assert result["by_status"].get("amended") == 1
    assert result["total_articles"] == 3


@pytest.mark.asyncio
async def test_compute_all_returns_report(db_session, metrics):
    result = await metrics.compute_all()

    assert result.population_health == {"by_status": {}, "total": 0}
    assert result.safety_public_order == {"complaint_calls": 0}
    assert "per_agent" in result.space_exploration
    assert "per_agent" in result.tool_exploration
    assert result.governance_conformity["voters"] == 0
    assert result.public_expression["total"] == 0
    assert result.social_fabric["total_relationships"] == 0
    assert result.economic_vitality["total_transactions"] == 0
    assert result.constitutional_growth["total_articles"] == 0


@pytest.mark.asyncio
async def test_gini_coefficient_edge_cases(metrics):
    assert metrics._gini([]) == 0.0
    assert metrics._gini([100]) == 0.0
    assert metrics._gini([0, 0, 0]) == 0.0
    gini_equal = metrics._gini([10, 10, 10])
    assert gini_equal == 0.0
    gini_unequal = metrics._gini([0, 0, 100])
    assert gini_unequal > 0.5
