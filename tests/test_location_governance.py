import uuid

import pytest
import pytest_asyncio

from emergent.db.models import ConstitutionArticle, Proposal, Vote
from emergent.tools.base import ToolResult
from emergent.tools.locations.governance import (
    CommentOnProposalTool,
    ListProposalsTool,
    ReadConstitutionTool,
    SubmitProposalTool,
    VoteOnProposalTool,
)


class MockAgent:
    def __init__(self, agent_id, name="TestAgent"):
        self.id = agent_id
        self.name = name


@pytest_asyncio.fixture
async def agent(db_session):
    from emergent.db.models import Agent as AgentModel
    a = AgentModel(name="TestAgent")
    db_session.add(a)
    await db_session.flush()
    return MockAgent(agent_id=a.id)


@pytest.mark.asyncio
class TestSubmitProposalTool:
    async def test_location_gate(self):
        assert SubmitProposalTool.location_gate == "Town Hall"

    async def test_execute_creates_proposal(self, db_session, agent):
        tool = SubmitProposalTool()
        result = await tool.execute(
            agent,
            {"title": "Test Proposal", "description": "A test", "category": "governance"},
            db_session,
            None,
        )
        assert result.success
        assert "proposal_id" in result.data

        prop = await db_session.get(Proposal, result.data["proposal_id"])
        assert prop is not None
        assert prop.title == "Test Proposal"
        assert prop.description == "A test"
        assert prop.category == "governance"
        assert prop.status == "submitted"
        assert prop.proposer_id == agent.id

    async def test_returns_tool_result(self, db_session, agent):
        tool = SubmitProposalTool()
        result = await tool.execute(
            agent,
            {"title": "T", "description": "D", "category": "others"},
            db_session,
            None,
        )
        assert isinstance(result, ToolResult)


@pytest.mark.asyncio
class TestVoteOnProposalTool:
    async def test_location_gate(self):
        assert VoteOnProposalTool.location_gate == "Town Hall"

    async def test_execute_creates_vote(self, db_session, agent):
        prop = Proposal(proposer_id=agent.id, title="Vote Test", status="submitted")
        db_session.add(prop)
        await db_session.flush()

        tool = VoteOnProposalTool()
        result = await tool.execute(
            agent,
            {"proposal_id": prop.id, "vote": "for"},
            db_session,
            None,
        )
        assert result.success
        assert result.data["vote"] == "for"

        vote = await db_session.execute(
            Vote.__table__.select().where(
                Vote.proposal_id == prop.id, Vote.agent_id == agent.id
            )
        )
        assert vote.scalar() is not None

    async def test_enforces_one_vote_per_agent(self, db_session, agent):
        prop = Proposal(proposer_id=agent.id, title="Unique Vote", status="submitted")
        db_session.add(prop)
        await db_session.flush()

        tool = VoteOnProposalTool()
        first = await tool.execute(
            agent,
            {"proposal_id": prop.id, "vote": "for"},
            db_session,
            None,
        )
        assert first.success

        second = await tool.execute(
            agent,
            {"proposal_id": prop.id, "vote": "against"},
            db_session,
            None,
        )
        assert not second.success
        assert "already voted" in second.error

    async def test_returns_tool_result(self, db_session, agent):
        prop = Proposal(proposer_id=agent.id, title="R", status="submitted")
        db_session.add(prop)
        await db_session.flush()

        tool = VoteOnProposalTool()
        result = await tool.execute(
            agent,
            {"proposal_id": prop.id, "vote": "against"},
            db_session,
            None,
        )
        assert isinstance(result, ToolResult)


@pytest.mark.asyncio
class TestReadConstitutionTool:
    async def test_location_gate(self):
        assert ReadConstitutionTool.location_gate == "Town Hall"

    async def test_execute_returns_active_articles(self, db_session, agent):
        db_session.add_all([
            ConstitutionArticle(article_number=1, title="Article I", content="Content one", status="active"),
            ConstitutionArticle(article_number=2, title="Article II", content="Content two", status="active"),
            ConstitutionArticle(article_number=3, title="Article III", content="Content three", status="archived"),
        ])
        await db_session.flush()

        tool = ReadConstitutionTool()
        result = await tool.execute(agent, {}, db_session, None)
        assert result.success
        assert len(result.data["articles"]) == 2

    async def test_returns_tool_result(self, db_session, agent):
        tool = ReadConstitutionTool()
        result = await tool.execute(agent, {}, db_session, None)
        assert isinstance(result, ToolResult)


@pytest.mark.asyncio
class TestCommentOnProposalTool:
    async def test_location_gate(self):
        assert CommentOnProposalTool.location_gate == "Town Hall"

    async def test_execute_appends_comment(self, db_session, agent):
        prop = Proposal(proposer_id=agent.id, title="Comment Test", description="Original", status="submitted")
        db_session.add(prop)
        await db_session.flush()

        tool = CommentOnProposalTool()
        result = await tool.execute(
            agent,
            {"proposal_id": prop.id, "comment": "Great idea!"},
            db_session,
            None,
        )
        assert result.success

        updated = await db_session.get(Proposal, prop.id)
        assert "Great idea!" in updated.description
        assert "TestAgent" in updated.description

    async def test_returns_error_for_missing_proposal(self, db_session, agent):
        tool = CommentOnProposalTool()
        result = await tool.execute(
            agent,
            {"proposal_id": 99999, "comment": "Hello"},
            db_session,
            None,
        )
        assert not result.success
        assert "not found" in result.error

    async def test_returns_tool_result(self, db_session, agent):
        prop = Proposal(proposer_id=agent.id, title="C", status="submitted")
        db_session.add(prop)
        await db_session.flush()

        tool = CommentOnProposalTool()
        result = await tool.execute(
            agent,
            {"proposal_id": prop.id, "comment": "Nice"},
            db_session,
            None,
        )
        assert isinstance(result, ToolResult)


@pytest.mark.asyncio
class TestListProposalsTool:
    async def test_location_gate(self):
        assert ListProposalsTool.location_gate == "Town Hall"

    async def test_execute_returns_all_proposals(self, db_session, agent):
        db_session.add_all([
            Proposal(proposer_id=agent.id, title="One", status="submitted"),
            Proposal(proposer_id=agent.id, title="Two", status="submitted"),
        ])
        await db_session.flush()

        tool = ListProposalsTool()
        result = await tool.execute(agent, {}, db_session, None)
        assert result.success
        assert len(result.data["proposals"]) == 2

    async def test_filter_by_status(self, db_session, agent):
        db_session.add_all([
            Proposal(proposer_id=agent.id, title="Passed", status="passed"),
            Proposal(proposer_id=agent.id, title="Rejected", status="rejected"),
            Proposal(proposer_id=agent.id, title="Submitted", status="submitted"),
        ])
        await db_session.flush()

        tool = ListProposalsTool()
        result = await tool.execute(agent, {"status": "passed"}, db_session, None)
        assert result.success
        assert len(result.data["proposals"]) == 1
        assert result.data["proposals"][0]["title"] == "Passed"

    async def test_returns_tool_result(self, db_session, agent):
        tool = ListProposalsTool()
        result = await tool.execute(agent, {}, db_session, None)
        assert isinstance(result, ToolResult)
