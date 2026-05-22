import uuid
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from emergent.db.models import Memory, DiaryEntry, Relationship


class MemoryManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_memory(self, agent_id: uuid.UUID, content: str, type_: str = "long_term") -> Memory:
        mem = Memory(agent_id=agent_id, content=content, type=type_)
        self.db.add(mem)
        await self.db.flush()
        return mem

    async def get_recent_memories(self, agent_id: uuid.UUID, limit: int = 20) -> list[Memory]:
        result = await self.db.execute(
            select(Memory)
            .where(Memory.agent_id == agent_id)
            .order_by(Memory.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_soul_entries(self, agent_id: uuid.UUID):
        from emergent.db.models import SoulEntry
        result = await self.db.execute(
            select(SoulEntry)
            .where(SoulEntry.agent_id == agent_id)
            .order_by(SoulEntry.created_at)
        )
        return list(result.scalars().all())

    async def write_diary(self, agent_id: uuid.UUID, content: dict, mood: str) -> DiaryEntry:
        entry = DiaryEntry(
            agent_id=agent_id,
            content=content,
            mood=mood,
            entry_date=date.today(),
        )
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def get_diary(self, agent_id: uuid.UUID, limit: int = 30) -> list[DiaryEntry]:
        result = await self.db.execute(
            select(DiaryEntry)
            .where(DiaryEntry.agent_id == agent_id)
            .order_by(DiaryEntry.entry_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def set_relationship(
        self,
        agent_id: uuid.UUID,
        target_id: uuid.UUID,
        rel_type: str = "neutral",
        trust: float = 0.5,
        notes: Optional[str] = None,
    ) -> Relationship:
        existing = await self.db.execute(
            select(Relationship).where(
                Relationship.agent_id == agent_id,
                Relationship.target_id == target_id,
            )
        )
        rel = existing.scalar_one_or_none()
        if rel:
            rel.relationship_type = rel_type
            rel.trust = trust
            rel.interaction_count += 1
            if notes:
                rel.notes = notes
        else:
            rel = Relationship(
                agent_id=agent_id,
                target_id=target_id,
                relationship_type=rel_type,
                trust=trust,
                interaction_count=1,
                notes=notes,
            )
            self.db.add(rel)
        await self.db.flush()
        return rel

    async def get_relationships(self, agent_id: uuid.UUID) -> list[Relationship]:
        result = await self.db.execute(
            select(Relationship).where(Relationship.agent_id == agent_id)
        )
        return list(result.scalars().all())

    async def get_relationship_summary(self, agent_id: uuid.UUID) -> str:
        rels = await self.get_relationships(agent_id)
        if not rels:
            return "No established relationships yet."
        parts = []
        for r in rels:
            parts.append(f"{r.relationship_type} (trust: {r.trust:.1f}, {r.interaction_count} interactions)")
        return "; ".join(parts)
