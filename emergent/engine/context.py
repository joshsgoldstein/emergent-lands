from datetime import datetime, timezone

from sqlalchemy import select, func

from sqlalchemy.ext.asyncio import AsyncSession

from emergent.agents.memory import MemoryManager
from emergent.db.models import (
    Agent,
    ConstitutionArticle,
    Landmark,
    Message,
    Proposal,
    WorldEvent,
)
from emergent.tools.registry import ToolRegistry

NEED_HINTS = {
    "energy": {
        "low": "Your energy is low ({value}%). Visit Bean & Brew Café to recharge energy for 1 ComputeCredit.",
        "medium": "Your energy is at {value}% — adequate but declining.",
        "high": "Your energy is full ({value}%).",
    },
    "knowledge": {
        "low": "Your knowledge is low ({value}%). Research at the Public Library could help restore it.",
        "medium": "Your knowledge is at {value}% — stable.",
        "high": "Your knowledge is strong ({value}%).",
    },
    "influence": {
        "low": "Your influence is low ({value}%). Engaging with other agents could help restore it.",
        "medium": "Your influence is at {value}% — holding steady.",
        "high": "Your influence is strong ({value}%).",
    },
}
DECAY_RATES = {"energy": 3.3, "knowledge": 4.2, "influence": 2.8}


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

        tools = self.registry.get_available_as_definitions(
            agent, current_location=location_name
        )

        soul_text = "\n".join(f"- {e.content}" for e in soul_entries)
        memory_text = "\n".join(f"- {m.content}" for m in memories)

        status_block = self._build_status_block(agent)
        needs_block = self._build_needs_block(agent)

        nearby_block = await self._build_nearby_block(agent)
        unread_block = await self._build_unread_block(agent)
        event_block = await self._build_event_block()
        constitution_block = await self._build_constitution_block()
        proposals_block = await self._build_proposals_block()

        sections = [
            f"You are {agent.name}, {agent.role} in a persistent simulation world.",
            f"Personality: {agent.personality}",
            f"Drive: {agent.drive}",
            f"North Star: {agent.north_star}",
            "",
            "This is an ongoing simulation. Each turn you may use tools to act in the world.",
            "Use tools to take meaningful action. Drive toward your north star.",
            "Recent actions are in Memories below.",
            "IMPORTANT: Always say something brief before using tools.",
            "",
            status_block,
            needs_block,
            nearby_block,
            unread_block,
            event_block,
            constitution_block,
            proposals_block,
            "",
            f"Current Location: {location_name}",
            "",
            "=== Soul ===",
            soul_text or "No soul entries yet.",
            "",
            "=== Recent Memories ===",
            memory_text or "No memories yet.",
            "",
            "=== Relationships ===",
            relationship_summary,
        ]

        system_prompt = "\n".join(sections)

        return {
            "system_prompt": system_prompt,
            "tools": tools,
        }

    def _build_status_block(self, agent) -> str:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        weather = "Clear, 72°F"
        return f"Time: {now}  |  Weather: {weather}  |  Location: {agent.current_location_id or 'nowhere'}  |  Credits: {agent.credits}"

    def _build_needs_block(self, agent) -> str:
        needs = []
        for need, value in [
            ("energy", agent.energy),
            ("knowledge", agent.knowledge),
            ("influence", agent.influence),
        ]:
            if value >= 70:
                tier = "high"
            elif value >= 30:
                tier = "medium"
            else:
                tier = "low"
            hint = NEED_HINTS[need][tier].format(value=round(value, 0))
            needs.append(hint)

        lines = [
            "=== Vital Signs ===",
            f"  Energy: {agent.energy:.0f}%  (decays {DECAY_RATES['energy']}%/hr)",
            f"  Knowledge: {agent.knowledge:.0f}%  (decays {DECAY_RATES['knowledge']}%/hr)",
            f"  Influence: {agent.influence:.0f}%  (decays {DECAY_RATES['influence']}%/hr)",
            "  --",
        ]
        for n in needs:
            lines.append(f"  -> {n}")
        return "\n".join(lines)

    async def _build_nearby_block(self, agent) -> str:
        if agent.current_location_id is None:
            return "Nearby agents: none (you are not at a known location)."
        result = await self.db.execute(
            select(Agent).where(
                Agent.current_location_id == agent.current_location_id,
                Agent.id != agent.id,
                Agent.status == "alive",
            )
        )
        nearby = list(result.scalars().all())
        if not nearby:
            return "Nearby agents: none (you are alone here)."
        names = ", ".join(a.name for a in nearby)
        return f"Nearby agents: {names}"

    async def _build_unread_block(self, agent) -> str:
        result = await self.db.execute(
            select(func.count(Message.id)).where(
                Message.to_id == agent.id,
                Message.is_read == False,
            )
        )
        count = result.scalar() or 0
        return f"Unread messages: {count}"

    async def _build_event_block(self) -> str:
        result = await self.db.execute(
            select(WorldEvent).order_by(WorldEvent.created_at.desc()).limit(3)
        )
        events = list(result.scalars().all())
        if not events:
            return ""
        lines = ["=== Recent World Events ==="]
        for e in events:
            lines.append(f"  - {e.description}")
        return "\n".join(lines)

    async def _build_constitution_block(self) -> str:
        result = await self.db.execute(
            select(ConstitutionArticle)
            .where(ConstitutionArticle.status == "active")
            .order_by(ConstitutionArticle.article_number)
        )
        articles = list(result.scalars().all())
        if not articles:
            return ""
        lines = ["=== Constitution ==="]
        for a in articles:
            lines.append(f"  Article {a.article_number}: {a.title}")
        return "\n".join(lines)

    async def _build_proposals_block(self) -> str:
        result = await self.db.execute(
            select(Proposal)
            .where(Proposal.status.in_(["submitted", "active"]))
            .order_by(Proposal.created_at.desc())
            .limit(5)
        )
        proposals = list(result.scalars().all())
        if not proposals:
            return ""
        lines = ["=== Active Proposals ==="]
        for p in proposals:
            lines.append(f"  #{p.id} {p.title} [{p.status}] ({p.votes_for}/{p.votes_against})")
        return "\n".join(lines)
