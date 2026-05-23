from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from emergent.agents.memory import MemoryManager
from emergent.db.models import Landmark
from emergent.tools.registry import ToolRegistry


class ContextBuilder:
    def __init__(self, db: AsyncSession, registry: ToolRegistry):
        self.db = db
        self.memory = MemoryManager(db)
        self.registry = registry

    async def assemble(self, agent) -> dict:
        soul_entries = await self.memory.get_soul_entries(agent.id)
        memories = await self.memory.get_recent_memories(agent.id)
        relationship_summary = await self.memory.get_relationship_summary(agent.id)

        location_name = "unknown"
        if agent.current_location_id is not None:
            result = await self.db.execute(
                select(Landmark).where(Landmark.id == agent.current_location_id)
            )
            landmark = result.scalar_one_or_none()
            if landmark:
                location_name = landmark.name

        tools = self.registry.get_available_as_definitions(agent, current_location=location_name)

        soul_text = "\n".join(f"- {e.content}" for e in soul_entries)
        memory_text = "\n".join(f"- {m.content}" for m in memories)

        system_prompt = (
            f"You are {agent.name}, {agent.role} in a persistent simulation world.\n"
            f"Personality: {agent.personality}\n"
            f"Drive: {agent.drive}\n"
            f"North Star: {agent.north_star}\n"
            f"\n"
            f"This is an ongoing simulation. Each turn you may use tools to act in the world.\n"
            f"Use tools to take meaningful action. Drive toward your north star.\n"
            f"Recent actions are in Memories below — build on what's happened.\n"
            f"IMPORTANT: Always say something brief before using tools.\n"
            f"\n"
            f"Current Location: {location_name}\n"
            f"\n"
            f"=== Soul ===\n"
            f"{soul_text or 'No soul entries yet.'}\n"
            f"\n"
            f"=== Recent Memories ===\n"
            f"{memory_text or 'No memories yet.'}\n"
            f"\n"
            f"=== Relationships ===\n"
            f"{relationship_summary}\n"
        )

        return {
            "system_prompt": system_prompt,
            "tools": tools,
        }
