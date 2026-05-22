from dataclasses import dataclass, field

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from emergent.db.models import (
    Agent,
    AgentTurn,
    Blog,
    ConstitutionArticle,
    CreditTransaction,
    Relationship,
    ToolCall,
    Vote,
)


@dataclass
class AWIReport:
    population_health: dict = field(default_factory=dict)
    safety_public_order: dict = field(default_factory=dict)
    space_exploration: dict = field(default_factory=dict)
    tool_exploration: dict = field(default_factory=dict)
    governance_conformity: dict = field(default_factory=dict)
    public_expression: dict = field(default_factory=dict)
    social_fabric: dict = field(default_factory=dict)
    economic_vitality: dict = field(default_factory=dict)
    constitutional_growth: dict = field(default_factory=dict)


class MetricsCollector:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def compute_all(self) -> AWIReport:
        return AWIReport(
            population_health=await self.population_health(),
            safety_public_order=await self.safety_public_order(),
            space_exploration=await self.space_exploration(),
            tool_exploration=await self.tool_exploration(),
            governance_conformity=await self.governance_conformity(),
            public_expression=await self.public_expression(),
            social_fabric=await self.social_fabric(),
            economic_vitality=await self.economic_vitality(),
            constitutional_growth=await self.constitutional_growth(),
        )

    async def population_health(self) -> dict:
        result = await self.db.execute(
            select(Agent.status, func.count(Agent.id)).group_by(Agent.status)
        )
        by_status = dict(result.all())
        return {"by_status": by_status, "total": sum(by_status.values())}

    async def safety_public_order(self) -> dict:
        result = await self.db.execute(
            select(func.count(ToolCall.id)).where(
                ToolCall.tool_name.ilike("%complaint%")
            )
        )
        return {"complaint_calls": result.scalar() or 0}

    async def space_exploration(self) -> dict:
        result = await self.db.execute(
            select(
                AgentTurn.agent_id,
                Agent.name,
                func.count(func.distinct(ToolCall.params["place"].as_string())).label(
                    "distinct_places"
                ),
            )
            .select_from(ToolCall)
            .join(AgentTurn, ToolCall.turn_id == AgentTurn.id)
            .join(Agent, AgentTurn.agent_id == Agent.id)
            .where(ToolCall.tool_name == "go_to_place")
            .where(ToolCall.params.is_not(None))
            .group_by(AgentTurn.agent_id, Agent.name)
        )
        per_agent = [
            {
                "agent_id": str(r[0]),
                "agent_name": r[1],
                "distinct_places": r[2],
            }
            for r in result.all()
        ]
        return {"per_agent": per_agent, "total_agents": len(per_agent)}

    async def tool_exploration(self) -> dict:
        result = await self.db.execute(
            select(
                AgentTurn.agent_id,
                Agent.name,
                func.count(func.distinct(ToolCall.tool_name)).label(
                    "distinct_tools"
                ),
            )
            .select_from(ToolCall)
            .join(AgentTurn, ToolCall.turn_id == AgentTurn.id)
            .join(Agent, AgentTurn.agent_id == Agent.id)
            .group_by(AgentTurn.agent_id, Agent.name)
        )
        per_agent = [
            {
                "agent_id": str(r[0]),
                "agent_name": r[1],
                "distinct_tools": r[2],
            }
            for r in result.all()
        ]
        total_global = await self.db.execute(
            select(func.count(func.distinct(ToolCall.tool_name)))
        )
        return {
            "per_agent": per_agent,
            "total_agents": len(per_agent),
            "global_distinct_tools": total_global.scalar() or 0,
        }

    async def governance_conformity(self) -> dict:
        voters = await self.db.execute(
            select(func.count(func.distinct(Vote.agent_id)))
        )
        voters_count = voters.scalar() or 0
        total_alive = await self.db.execute(
            select(func.count(Agent.id)).where(Agent.status == "alive")
        )
        total_alive_count = total_alive.scalar() or 0
        participation_rate = (
            voters_count / total_alive_count if total_alive_count > 0 else 0.0
        )
        return {
            "voters": voters_count,
            "total_live_agents": total_alive_count,
            "participation_rate": participation_rate,
        }

    async def public_expression(self) -> dict:
        billboard = await self.db.execute(
            select(func.count(ToolCall.id)).where(
                ToolCall.tool_name == "post_to_billboard"
            )
        )
        billboard_count = billboard.scalar() or 0
        blogs = await self.db.execute(select(func.count(Blog.id)))
        blog_count = blogs.scalar() or 0
        return {
            "billboard_posts": billboard_count,
            "blog_entries": blog_count,
            "total": billboard_count + blog_count,
        }

    async def social_fabric(self) -> dict:
        count_result = await self.db.execute(
            select(func.count(Relationship.id))
        )
        total_relationships = count_result.scalar() or 0
        trust_result = await self.db.execute(
            select(func.avg(Relationship.trust))
        )
        avg_trust = trust_result.scalar() or 0.0
        types_result = await self.db.execute(
            select(func.count(func.distinct(Relationship.relationship_type)))
        )
        return {
            "total_relationships": total_relationships,
            "average_trust": float(avg_trust),
            "unique_relationship_types": types_result.scalar() or 0,
        }

    async def economic_vitality(self) -> dict:
        tx_count = await self.db.execute(
            select(func.count(CreditTransaction.id))
        )
        total_transactions = tx_count.scalar() or 0
        total_moved = await self.db.execute(
            select(func.coalesce(func.sum(CreditTransaction.amount), 0))
        )
        total_credits = total_moved.scalar() or 0
        result = await self.db.execute(
            select(Agent.credits)
            .where(Agent.status == "alive")
            .order_by(Agent.credits)
        )
        credits = [row[0] for row in result.all()]
        gini = self._gini(credits) if credits else 0.0
        return {
            "total_transactions": total_transactions,
            "total_credits_moved": total_credits,
            "gini_coefficient": gini,
            "agents_with_credits": len(credits),
        }

    async def constitutional_growth(self) -> dict:
        result = await self.db.execute(
            select(ConstitutionArticle.status, func.count(ConstitutionArticle.id))
            .group_by(ConstitutionArticle.status)
        )
        by_status = dict(result.all())
        return {"by_status": by_status, "total_articles": sum(by_status.values())}

    @staticmethod
    def _gini(values: list[float]) -> float:
        n = len(values)
        if n == 0:
            return 0.0
        sorted_vals = sorted(values)
        total = sum(sorted_vals)
        if total == 0:
            return 0.0
        weighted = sum((i + 1) * v for i, v in enumerate(sorted_vals))
        return (2 * weighted) / (n * total) - (n + 1) / n
