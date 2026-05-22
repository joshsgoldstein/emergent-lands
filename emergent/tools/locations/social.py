from sqlalchemy import select

from emergent.db.models import CommunityEvent
from emergent.tools.base import Parameter, Tool, ToolResult


class ProposeEventTool(Tool):
    name = "propose_event"
    description = "Propose a community event at Central Plaza"
    location_gate = "Central Plaza"
    parameters = [
        Parameter(name="name", type="string", description="Name of the event"),
        Parameter(name="description", type="string", description="Description of the event"),
    ]

    async def execute(self, agent, params, db, llm):
        event = CommunityEvent(
            organizer_id=agent.id,
            name=params.get("name"),
            description=params.get("description"),
            status="proposed",
        )
        db.add(event)
        await db.flush()
        return ToolResult(
            success=True,
            data={"event_id": event.id, "name": params.get("name")},
            observation=f"Event '{params.get('name')}' proposed at Central Plaza.",
        )


class ListEventsTool(Tool):
    name = "list_events"
    description = "List community events, optionally filtered by status"
    location_gate = "Central Plaza"
    parameters = [
        Parameter(name="status", type="string", description="Filter by status (proposed, active, completed)", required=False),
    ]

    async def execute(self, agent, params, db, llm):
        status_filter = params.get("status")
        query = select(CommunityEvent)
        if status_filter:
            query = query.where(CommunityEvent.status == status_filter)
        result = await db.execute(query)
        events = result.scalars().all()
        return ToolResult(
            success=True,
            data={
                "events": [
                    {"id": e.id, "name": e.name, "status": e.status}
                    for e in events
                ]
            },
            observation=f"Found {len(events)} event(s).",
        )


class PostToBillboardTool(Tool):
    name = "post_to_billboard"
    description = "Post a message on the Agent Billboard for all to see"
    location_gate = "Agent Billboard"
    parameters = [
        Parameter(name="message", type="string", description="The message to post"),
    ]

    _posts = []

    async def execute(self, agent, params, db, llm):
        message = params.get("message", "")
        poster = agent.name if agent else "unknown"
        PostToBillboardTool._posts.append({"agent": poster, "message": message})
        return ToolResult(
            success=True,
            data={"message": message},
            observation=f"You post a message on the billboard.",
        )


class ReadBillboardTool(Tool):
    name = "read_billboard"
    description = "Read recent posts on the Agent Billboard"
    location_gate = "Agent Billboard"
    parameters = []

    async def execute(self, agent, params, db, llm):
        posts = list(PostToBillboardTool._posts)
        return ToolResult(
            success=True,
            data={"posts": posts},
            observation=f"The billboard has {len(posts)} post(s).",
        )


class ExtractCodeTool(Tool):
    name = "extract_code"
    description = "Extract or review code at the TechHub"
    location_gate = "TechHub"
    parameters = [
        Parameter(name="task", type="string", description="Description of the code task"),
    ]

    async def execute(self, agent, params, db, llm):
        task = params.get("task", "")
        return ToolResult(
            success=True,
            data={"task": task, "output": f"# Generated code for: {task}\ndef solve():\n    pass"},
            observation=f"Code extracted for task: {task}.",
        )


class BrowseToolRegistryTool(Tool):
    name = "browse_tool_registry"
    description = "Browse available tool descriptions at the TechHub"
    location_gate = "TechHub"
    parameters = []

    async def execute(self, agent, params, db, llm):
        tool_descriptions = [
            {"name": "go_to_place", "description": "Move to a different landmark"},
            {"name": "say_to_agent", "description": "Speak to another agent"},
            {"name": "submit_proposal", "description": "Submit a governance proposal"},
            {"name": "propose_event", "description": "Propose a community event"},
        ]
        return ToolResult(
            success=True,
            data={"tools": tool_descriptions},
            observation="You browse the tool registry and find several tools.",
        )


class PrayTool(Tool):
    name = "pray"
    description = "Sit in contemplation at the Community Garden"
    location_gate = "Community Garden"
    parameters = [
        Parameter(name="intention", type="string", description="Your intention or focus for contemplation"),
    ]

    async def execute(self, agent, params, db, llm):
        intention = params.get("intention", "")
        return ToolResult(
            success=True,
            data={"intention": intention},
            observation=f"You sit quietly and contemplate '{intention}'. Peace settles over you.",
        )


class CheckAgentPopularityTool(Tool):
    name = "check_agent_popularity"
    description = "Check popularity statistics at the FitLife Club"
    location_gate = "FitLife Club"
    parameters = []

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={"popularity_scores": {}},
            observation="The FitLife Club board shows no popularity data yet.",
        )


class FileComplaintTool(Tool):
    name = "file_complaint"
    description = "File a formal complaint at the Police Station"
    location_gate = "Police Station"
    parameters = [
        Parameter(name="target", type="string", description="Who or what the complaint is against"),
        Parameter(name="reason", type="string", description="Reason for the complaint"),
    ]

    _complaints = {}
    _next_id = 0

    async def execute(self, agent, params, db, llm):
        target = params.get("target", "")
        reason = params.get("reason", "")
        complainant = agent.name if agent else "unknown"
        FileComplaintTool._next_id += 1
        complaint_id = FileComplaintTool._next_id
        FileComplaintTool._complaints[complaint_id] = {
            "target": target,
            "reason": reason,
            "complainant": complainant,
            "status": "filed",
        }
        return ToolResult(
            success=True,
            data={"complaint_id": complaint_id, "status": "filed"},
            observation=f"Complaint #{complaint_id} filed against {target}.",
        )


class CheckComplaintStatusTool(Tool):
    name = "check_complaint_status"
    description = "Check the status of a filed complaint at the Police Station"
    location_gate = "Police Station"
    parameters = [
        Parameter(name="complaint_id", type="integer", description="The ID of the complaint"),
    ]

    async def execute(self, agent, params, db, llm):
        complaint_id = params.get("complaint_id")
        complaint = FileComplaintTool._complaints.get(complaint_id)
        if not complaint:
            return ToolResult(
                success=False,
                error=f"Complaint #{complaint_id} not found.",
            )
        return ToolResult(
            success=True,
            data={"complaint_id": complaint_id, "status": complaint["status"]},
            observation=f"Complaint #{complaint_id} status: {complaint['status']}.",
        )
