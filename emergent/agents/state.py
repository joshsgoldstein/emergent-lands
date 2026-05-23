import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from emergent.db.models import Agent, SoulEntry


class AgentStateManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_agent(
        self,
        name: str,
        role: str = "",
        personality: str = "",
        drive: str = "",
        north_star: str = "",
        home: Optional[str] = None,
    ) -> Agent:
        agent = Agent(
            id=uuid.uuid4(),
            name=name,
            role=role,
            personality=personality,
            drive=drive,
            north_star=north_star,
            energy=100.0,
            knowledge=100.0,
            influence=100.0,
            credits=10,
        )
        if home:
            agent.home_location_name = home
        self.db.add(agent)
        await self.db.flush()

        if home:
            from emergent.db.models import Landmark
            result = await self.db.execute(select(Landmark).where(Landmark.name == home))
            landmark = result.scalar_one_or_none()
            if landmark:
                agent.current_location_id = landmark.id
                await self.db.flush()

        return agent

    async def seed_soul_entries(self, agent_id: uuid.UUID, entries: list[str]):
        for content in entries:
            self.db.add(SoulEntry(agent_id=agent_id, content=content))
        await self.db.flush()

    async def get_agent(self, agent_id: uuid.UUID) -> Optional[Agent]:
        result = await self.db.execute(select(Agent).where(Agent.id == agent_id))
        return result.scalar_one_or_none()

    async def get_agent_by_name(self, name: str) -> Optional[Agent]:
        result = await self.db.execute(select(Agent).where(Agent.name == name))
        return result.scalar_one_or_none()

    async def get_living_agents(self) -> list[Agent]:
        result = await self.db.execute(
            select(Agent).where(Agent.status == "alive").order_by(Agent.name)
        )
        return list(result.scalars().all())

    DECAY_RATES = {
        "energy": 3.3,
        "knowledge": 4.2,
        "influence": 2.8,
    }

    async def apply_needs_decay(self, agent: Agent, hours_passed: float = 1.0):
        agent.energy = max(0.0, agent.energy - self.DECAY_RATES["energy"] * hours_passed)
        agent.knowledge = max(0.0, agent.knowledge - self.DECAY_RATES["knowledge"] * hours_passed)
        agent.influence = max(0.0, agent.influence - self.DECAY_RATES["influence"] * hours_passed)
        if agent.energy <= 0:
            agent.status = "dead"
        await self.db.flush()

    async def update_location(self, agent: Agent, landmark_name: str):
        from emergent.db.models import Landmark
        result = await self.db.execute(select(Landmark).where(Landmark.name == landmark_name))
        landmark = result.scalar_one_or_none()
        if landmark:
            agent.current_location_id = landmark.id
            await self.db.flush()

    async def update_mood(self, agent: Agent, mood: str):
        agent.mood = mood
        await self.db.flush()
