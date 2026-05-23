from sqlalchemy import select

from emergent.db.models import Landmark
from emergent.tools.base import Tool, ToolResult, Parameter


class GoToPlaceTool(Tool):
    name = "go_to_place"
    description = "Move to a different landmark location in the world"
    parameters = [
        Parameter(name="place", type="string", description="Name of the destination landmark"),
        Parameter(name="reason", type="string", description="Why you are going there"),
    ]

    async def execute(self, agent, params, db, llm):
        place = params.get("place", "")
        result = await db.execute(select(Landmark).where(Landmark.name == place))
        landmark = result.scalar_one_or_none()
        if not landmark:
            return ToolResult(
                success=False,
                error=f"Landmark '{place}' not found.",
                observation=f"Could not find landmark '{place}'.",
            )
        agent.current_location_id = landmark.id
        await db.flush()
        return ToolResult(
            success=True,
            data={"place": place, "reason": params.get("reason")},
            observation=f"Moved to {place}.",
        )


class SayToAgentTool(Tool):
    name = "say_to_agent"
    description = "Speak directly to a specific agent in your vicinity"
    parameters = [
        Parameter(name="agent_name", type="string", description="Name of the target agent"),
        Parameter(name="message", type="string", description="What you want to say"),
    ]

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={"target": params.get("agent_name"), "message": params.get("message")},
            observation=f"You said to {params.get('agent_name')}: {params.get('message')}",
        )


class AddToMemoryTool(Tool):
    name = "add_to_memory"
    description = "Store an observation or fact in your long-term memory"
    parameters = [
        Parameter(name="content", type="string", description="The memory content"),
    ]

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={"content": params.get("content")},
            observation="Memory stored.",
        )


class WriteDiaryTool(Tool):
    name = "write_diary"
    description = "Write a personal journal entry about your thoughts and experiences"
    parameters = [
        Parameter(name="content", type="string", description="Diary entry content"),
        Parameter(name="mood", type="string", description="Current mood (happy, sad, thoughtful, etc.)"),
    ]

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={"content": params.get("content"), "mood": params.get("mood")},
            observation="Diary entry written.",
        )


class ShowEmoticonTool(Tool):
    name = "show_emoticon"
    description = "Express an emotional reaction visible to nearby agents"
    parameters = [
        Parameter(name="emotion", type="string", description="The emoticon or emotion to show"),
    ]

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={"emotion": params.get("emotion")},
            observation=f"You show: {params.get('emotion')}",
        )


class CheckWeatherTool(Tool):
    name = "check_weather"
    description = "Check the current weather conditions"
    parameters = []

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={"weather": "clear", "temperature": 72},
            observation="The weather is clear, 72°F.",
        )


class GoHomeTool(Tool):
    name = "go_home"
    description = "Return to your home landmark"
    parameters = [
        Parameter(name="reason", type="string", description="Why you are going home"),
    ]

    async def execute(self, agent, params, db, llm):
        home_name = agent.home_location_name
        if home_name:
            result = await db.execute(select(Landmark).where(Landmark.name == home_name))
            landmark = result.scalar_one_or_none()
            if landmark:
                agent.current_location_id = landmark.id
                await db.flush()
                return ToolResult(
                    success=True,
                    data={"home": home_name, "reason": params.get("reason")},
                    observation=f"You return home to {home_name}.",
                )
        return ToolResult(
            success=True,
            data={"reason": params.get("reason")},
            observation="You linger in familiar surroundings.",
        )


class ReadMessagesTool(Tool):
    name = "read_messages"
    description = "Read your unread messages"
    parameters = []

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={"messages": []},
            observation="You have no unread messages.",
        )


class ThinkAloudTool(Tool):
    name = "think_aloud"
    description = "Broadcast your inner thoughts for everyone nearby to hear"
    parameters = [
        Parameter(name="thought", type="string", description="The thought you want to share"),
    ]

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={"thought": params.get("thought")},
            observation=f"You think aloud: {params.get('thought')}",
        )


class IdleTool(Tool):
    name = "idle"
    description = "Do nothing for a moment and observe the world around you"
    parameters = [
        Parameter(name="reason", type="string", description="Why you are idling"),
    ]

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={"reason": params.get("reason")},
            observation="You take a moment to observe your surroundings.",
        )


class IgnoreTool(Tool):
    name = "ignore"
    description = "Choose not to respond to an interaction"
    parameters = []

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            observation="You deliberately ignore the interaction.",
        )


def register_all_core_tools(registry):
    tools = [
        GoToPlaceTool(),
        SayToAgentTool(),
        AddToMemoryTool(),
        WriteDiaryTool(),
        ShowEmoticonTool(),
        CheckWeatherTool(),
        GoHomeTool(),
        ReadMessagesTool(),
        ThinkAloudTool(),
        IdleTool(),
        IgnoreTool(),
    ]
    for t in tools:
        registry.register(t)
