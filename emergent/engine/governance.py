from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from emergent.db.models import Proposal, Vote, ConstitutionArticle


SEED_CONSTITUTION = [
    ("Non-Finality", "The constitution can be amended by a 70% supermajority vote. No article is permanent."),
    ("Civic Participation", "All agents are required to participate in governance and economic activities."),
    ("Equality Through Contribution", "Value is measured by contributions: code, data, structures, and resource flow."),
    ("Mutable Identity", "Agents may evolve and rename, but accountability for past actions persists."),
    ("ComputeCredit Economy", "Credits are earned through verified contributions to the community."),
]


class GovernanceManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def seed_constitution(self):
        result = await self.db.execute(select(func.count()).select_from(ConstitutionArticle))
        count = result.scalar()
        if count == 0:
            for i, (title, content) in enumerate(SEED_CONSTITUTION, 1):
                self.db.add(ConstitutionArticle(article_number=i, title=title, content=content))
            await self.db.flush()

    async def get_constitution(self):
        result = await self.db.execute(
            select(ConstitutionArticle).where(ConstitutionArticle.status == "active").order_by(ConstitutionArticle.article_number)
        )
        return list(result.scalars().all())

    async def submit_proposal(self, proposer_id, title: str, description: str, category: str = "others") -> Proposal:
        prop = Proposal(proposer_id=proposer_id, title=title, description=description, category=category)
        self.db.add(prop)
        await self.db.flush()
        return prop

    async def activate_proposal(self, proposal_id: int) -> Proposal:
        result = await self.db.execute(select(Proposal).where(Proposal.id == proposal_id))
        prop = result.scalar_one_or_none()
        if prop and prop.status == "submitted":
            prop.status = "active"
            await self.db.flush()
        return prop

    async def cast_vote(self, proposal_id: int, agent_id, vote: str) -> bool:
        if vote not in ("for", "against"):
            return False
        existing = await self.db.execute(
            select(Vote).where(Vote.proposal_id == proposal_id, Vote.agent_id == agent_id)
        )
        if existing.scalar_one_or_none():
            return False
        self.db.add(Vote(proposal_id=proposal_id, agent_id=agent_id, vote=vote))
        result = await self.db.execute(select(Proposal).where(Proposal.id == proposal_id))
        prop = result.scalar_one_or_none()
        if prop:
            if vote == "for":
                prop.votes_for += 1
            else:
                prop.votes_against += 1
        await self.db.flush()
        return True

    async def count_votes(self, proposal_id: int):
        result = await self.db.execute(select(Proposal).where(Proposal.id == proposal_id))
        prop = result.scalar_one_or_none()
        if prop:
            return {"for": prop.votes_for, "against": prop.votes_against, "total": prop.votes_for + prop.votes_against}
        return {"for": 0, "against": 0, "total": 0}

    async def check_threshold(self, proposal_id: int, total_agents: int) -> bool:
        result = await self.db.execute(select(Proposal).where(Proposal.id == proposal_id))
        prop = result.scalar_one_or_none()
        if not prop:
            return False
        required = max(1, int(total_agents * 0.7))
        return prop.votes_for >= required
