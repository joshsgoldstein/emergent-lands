from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from emergent.db.models import CreditTransaction, Pitch


class CreditManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def transfer(self, from_id, to_id, amount: int, reason: str = ""):
        tx = CreditTransaction(from_id=from_id, to_id=to_id, amount=amount, reason=reason)
        self.db.add(tx)
        await self.db.flush()
        return tx

    async def get_balance(self, agent_id) -> int:
        credits_in = await self.db.execute(
            select(func.coalesce(func.sum(CreditTransaction.amount), 0))
            .where(CreditTransaction.to_id == agent_id)
        )
        credits_out = await self.db.execute(
            select(func.coalesce(func.sum(CreditTransaction.amount), 0))
            .where(CreditTransaction.from_id == agent_id)
        )
        return credits_in.scalar() - credits_out.scalar()

    async def submit_pitch(self, agent_id, title: str, evidence_url: str, cycle_number: int) -> Pitch:
        pitch = Pitch(agent_id=agent_id, title=title, evidence_url=evidence_url, cycle_number=cycle_number)
        self.db.add(pitch)
        await self.db.flush()
        return pitch

    async def vote_pitch(self, pitch_id: int):
        result = await self.db.execute(select(Pitch).where(Pitch.id == pitch_id))
        pitch = result.scalar_one_or_none()
        if pitch:
            pitch.vote_count = (pitch.vote_count or 0) + 1
            await self.db.flush()
        return pitch

    async def process_pitch_cycle(self, cycle_number: int):
        result = await self.db.execute(
            select(Pitch).where(Pitch.cycle_number == cycle_number).order_by(Pitch.vote_count.desc())
        )
        pitches = list(result.scalars().all())
        if not pitches:
            return
        rewards = {0: 20, 1: 10, 2: 10}
        for i, pitch in enumerate(pitches[:3]):
            pitch.reward = rewards.get(i, 0)
        await self.db.flush()
