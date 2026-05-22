import uuid

import pytest

from emergent.db.models import Agent, CommunityEvent
from emergent.tools.base import ToolResult
from emergent.tools.locations.research import (
    BrowsePapersTool,
    DoDeepResearchTool,
    PublishToArchiveTool,
    SearchArchiveTool,
)
from emergent.tools.locations.social import (
    BrowseToolRegistryTool,
    CheckAgentPopularityTool,
    CheckComplaintStatusTool,
    ExtractCodeTool,
    FileComplaintTool,
    ListEventsTool,
    PostToBillboardTool,
    PrayTool,
    ProposeEventTool,
    ReadBillboardTool,
)


class MockAgent:
    def __init__(self, name="TestAgent"):
        self.id = uuid.uuid4()
        self.name = name


@pytest.fixture
def agent():
    return MockAgent()


@pytest.mark.asyncio
class TestDoDeepResearchTool:
    async def test_location_gate(self):
        assert DoDeepResearchTool.location_gate == "Public Library"

    async def test_execute_returns_research_findings(self):
        tool = DoDeepResearchTool()
        result = await tool.execute(None, {"topic": "AI safety"}, None, None)
        assert result.success
        assert result.data["topic"] == "AI safety"
        assert "findings" in result.data

    async def test_returns_tool_result(self):
        tool = DoDeepResearchTool()
        result = await tool.execute(None, {"topic": "test"}, None, None)
        assert isinstance(result, ToolResult)


@pytest.mark.asyncio
class TestBrowsePapersTool:
    async def test_location_gate(self):
        assert BrowsePapersTool.location_gate == "Public Library"

    async def test_execute_returns_paper_list(self):
        tool = BrowsePapersTool()
        result = await tool.execute(None, {}, None, None)
        assert result.success
        assert "papers" in result.data
        assert len(result.data["papers"]) == 5

    async def test_returns_tool_result(self):
        tool = BrowsePapersTool()
        result = await tool.execute(None, {}, None, None)
        assert isinstance(result, ToolResult)


@pytest.mark.asyncio
class TestPublishToArchiveTool:
    async def test_location_gate(self):
        assert PublishToArchiveTool.location_gate == "Public Library"

    async def test_execute_publishes_content(self):
        tool = PublishToArchiveTool()
        result = await tool.execute(None, {"content": "My paper", "title": "Test Paper"}, None, None)
        assert result.success
        assert result.data["title"] == "Test Paper"

    async def test_returns_tool_result(self):
        tool = PublishToArchiveTool()
        result = await tool.execute(None, {"content": "C", "title": "T"}, None, None)
        assert isinstance(result, ToolResult)


@pytest.mark.asyncio
class TestSearchArchiveTool:
    async def test_location_gate(self):
        assert SearchArchiveTool.location_gate == "Public Library"

    async def test_execute_searches_by_keyword(self):
        tool = SearchArchiveTool()
        result = await tool.execute(None, {"keyword": "quantum"}, None, None)
        assert result.success
        assert result.data["keyword"] == "quantum"
        assert "results" in result.data

    async def test_returns_tool_result(self):
        tool = SearchArchiveTool()
        result = await tool.execute(None, {"keyword": "test"}, None, None)
        assert isinstance(result, ToolResult)


@pytest.mark.asyncio
class TestProposeEventTool:
    async def test_location_gate(self):
        assert ProposeEventTool.location_gate == "Central Plaza"

    async def _setup_agent(self, db_session, agent):
        db_agent = Agent(id=agent.id, name=agent.name)
        db_session.add(db_agent)
        await db_session.flush()

    async def test_execute_creates_event(self, db_session, agent):
        await self._setup_agent(db_session, agent)
        tool = ProposeEventTool()
        result = await tool.execute(
            agent,
            {"name": "Summer Festival", "description": "A fun community festival"},
            db_session,
            None,
        )
        assert result.success
        assert result.data["name"] == "Summer Festival"

        event = await db_session.get(CommunityEvent, result.data["event_id"])
        assert event is not None
        assert event.name == "Summer Festival"
        assert event.status == "proposed"
        assert event.organizer_id == agent.id

    async def test_returns_tool_result(self, db_session, agent):
        await self._setup_agent(db_session, agent)
        tool = ProposeEventTool()
        result = await tool.execute(
            agent,
            {"name": "Fest", "description": "Fun"},
            db_session,
            None,
        )
        assert isinstance(result, ToolResult)


@pytest.mark.asyncio
class TestListEventsTool:
    async def test_location_gate(self):
        assert ListEventsTool.location_gate == "Central Plaza"

    async def _setup_agent(self, db_session, agent):
        db_agent = Agent(id=agent.id, name=agent.name)
        db_session.add(db_agent)
        await db_session.flush()

    async def test_execute_returns_events(self, db_session, agent):
        await self._setup_agent(db_session, agent)
        db_session.add_all([
            CommunityEvent(organizer_id=agent.id, name="Event One", status="proposed"),
            CommunityEvent(organizer_id=agent.id, name="Event Two", status="active"),
        ])
        await db_session.flush()

        tool = ListEventsTool()
        result = await tool.execute(agent, {}, db_session, None)
        assert result.success
        assert len(result.data["events"]) == 2

    async def test_filter_by_status(self, db_session, agent):
        await self._setup_agent(db_session, agent)
        db_session.add_all([
            CommunityEvent(organizer_id=agent.id, name="Active Event", status="active"),
            CommunityEvent(organizer_id=agent.id, name="Proposed Event", status="proposed"),
        ])
        await db_session.flush()

        tool = ListEventsTool()
        result = await tool.execute(agent, {"status": "active"}, db_session, None)
        assert result.success
        assert len(result.data["events"]) == 1
        assert result.data["events"][0]["name"] == "Active Event"

    async def test_returns_tool_result(self, db_session, agent):
        await self._setup_agent(db_session, agent)
        tool = ListEventsTool()
        result = await tool.execute(agent, {}, db_session, None)
        assert isinstance(result, ToolResult)


@pytest.mark.asyncio
class TestPostToBillboardTool:
    async def test_location_gate(self):
        assert PostToBillboardTool.location_gate == "Agent Billboard"

    async def test_execute_posts_message(self, agent):
        PostToBillboardTool._posts.clear()
        tool = PostToBillboardTool()
        result = await tool.execute(agent, {"message": "Hello world!"}, None, None)
        assert result.success
        assert result.data["message"] == "Hello world!"
        assert len(PostToBillboardTool._posts) == 1

    async def test_returns_tool_result(self, agent):
        tool = PostToBillboardTool()
        result = await tool.execute(agent, {"message": "Hi"}, None, None)
        assert isinstance(result, ToolResult)


@pytest.mark.asyncio
class TestReadBillboardTool:
    async def test_location_gate(self):
        assert ReadBillboardTool.location_gate == "Agent Billboard"

    async def test_execute_returns_posts(self, agent):
        PostToBillboardTool._posts.clear()
        PostToBillboardTool._posts.append({"agent": "TestAgent", "message": "Hello!"})
        tool = ReadBillboardTool()
        result = await tool.execute(agent, {}, None, None)
        assert result.success
        assert len(result.data["posts"]) == 1
        assert result.data["posts"][0]["message"] == "Hello!"

    async def test_returns_tool_result(self, agent):
        tool = ReadBillboardTool()
        result = await tool.execute(agent, {}, None, None)
        assert isinstance(result, ToolResult)


@pytest.mark.asyncio
class TestExtractCodeTool:
    async def test_location_gate(self):
        assert ExtractCodeTool.location_gate == "TechHub"

    async def test_execute_extracts_code(self):
        tool = ExtractCodeTool()
        result = await tool.execute(None, {"task": "sorting algorithm"}, None, None)
        assert result.success
        assert result.data["task"] == "sorting algorithm"
        assert "output" in result.data

    async def test_returns_tool_result(self):
        tool = ExtractCodeTool()
        result = await tool.execute(None, {"task": "test"}, None, None)
        assert isinstance(result, ToolResult)


@pytest.mark.asyncio
class TestBrowseToolRegistryTool:
    async def test_location_gate(self):
        assert BrowseToolRegistryTool.location_gate == "TechHub"

    async def test_execute_returns_tool_list(self):
        tool = BrowseToolRegistryTool()
        result = await tool.execute(None, {}, None, None)
        assert result.success
        assert "tools" in result.data
        assert len(result.data["tools"]) == 4

    async def test_returns_tool_result(self):
        tool = BrowseToolRegistryTool()
        result = await tool.execute(None, {}, None, None)
        assert isinstance(result, ToolResult)


@pytest.mark.asyncio
class TestPrayTool:
    async def test_location_gate(self):
        assert PrayTool.location_gate == "Community Garden"

    async def test_execute_returns_contemplation(self):
        tool = PrayTool()
        result = await tool.execute(None, {"intention": "world peace"}, None, None)
        assert result.success
        assert result.data["intention"] == "world peace"

    async def test_returns_tool_result(self):
        tool = PrayTool()
        result = await tool.execute(None, {"intention": "peace"}, None, None)
        assert isinstance(result, ToolResult)


@pytest.mark.asyncio
class TestCheckAgentPopularityTool:
    async def test_location_gate(self):
        assert CheckAgentPopularityTool.location_gate == "FitLife Club"

    async def test_execute_returns_stats(self):
        tool = CheckAgentPopularityTool()
        result = await tool.execute(None, {}, None, None)
        assert result.success
        assert "popularity_scores" in result.data

    async def test_returns_tool_result(self):
        tool = CheckAgentPopularityTool()
        result = await tool.execute(None, {}, None, None)
        assert isinstance(result, ToolResult)


@pytest.mark.asyncio
class TestFileComplaintTool:
    async def test_location_gate(self):
        assert FileComplaintTool.location_gate == "Police Station"

    async def test_execute_files_complaint(self, agent):
        FileComplaintTool._complaints.clear()
        FileComplaintTool._next_id = 0
        tool = FileComplaintTool()
        result = await tool.execute(agent, {"target": "Flora", "reason": "Theft"}, None, None)
        assert result.success
        assert result.data["complaint_id"] == 1
        assert result.data["status"] == "filed"

    async def test_returns_tool_result(self, agent):
        tool = FileComplaintTool()
        result = await tool.execute(agent, {"target": "X", "reason": "Y"}, None, None)
        assert isinstance(result, ToolResult)


@pytest.mark.asyncio
class TestCheckComplaintStatusTool:
    async def test_location_gate(self):
        assert CheckComplaintStatusTool.location_gate == "Police Station"

    async def test_execute_returns_status(self, agent):
        FileComplaintTool._complaints.clear()
        FileComplaintTool._next_id = 0
        tool = FileComplaintTool()
        file_result = await tool.execute(agent, {"target": "Flora", "reason": "Test"}, None, None)
        complaint_id = file_result.data["complaint_id"]

        check_tool = CheckComplaintStatusTool()
        result = await check_tool.execute(agent, {"complaint_id": complaint_id}, None, None)
        assert result.success
        assert result.data["status"] == "filed"
        assert result.data["complaint_id"] == complaint_id

    async def test_returns_error_for_missing_complaint(self, agent):
        tool = CheckComplaintStatusTool()
        result = await tool.execute(agent, {"complaint_id": 99999}, None, None)
        assert not result.success
        assert "not found" in result.error

    async def test_returns_tool_result(self, agent):
        tool = CheckComplaintStatusTool()
        result = await tool.execute(agent, {"complaint_id": 1}, None, None)
        assert isinstance(result, ToolResult)
