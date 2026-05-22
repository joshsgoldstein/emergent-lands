from sqlalchemy import select

from emergent.db.models import Agent, Pitch, CreditTransaction
from emergent.tools.base import Tool, ToolResult, Parameter


class SubmitPitchTool(Tool):
    name = "submit_pitch"
    description = "Submit a ComputeCredits pitch with evidence URL for community voting"
    location_gate = "Victory Arch"
    parameters = [
        Parameter(name="title", type="string", description="Title of the pitch"),
        Parameter(name="evidence_url", type="string", description="URL with supporting evidence"),
        Parameter(name="cycle_number", type="integer", description="The funding cycle number"),
    ]

    async def execute(self, agent, params, db, llm):
        pitch = Pitch(
            agent_id=agent.id,
            title=params.get("title"),
            evidence_url=params.get("evidence_url"),
            cycle_number=params.get("cycle_number"),
        )
        db.add(pitch)
        await db.flush()
        return ToolResult(
            success=True,
            data={"pitch_id": pitch.id},
            observation=f"Pitch '{params.get('title')}' submitted for cycle {params.get('cycle_number')}.",
        )


class VoteForPitchTool(Tool):
    name = "vote_for_pitch"
    description = "Vote for a pitch to support it in the current funding cycle"
    location_gate = "Victory Arch"
    parameters = [
        Parameter(name="pitch_id", type="integer", description="ID of the pitch to vote for"),
    ]

    async def execute(self, agent, params, db, llm):
        pitch = await db.get(Pitch, params.get("pitch_id"))
        if pitch is None:
            return ToolResult(
                success=False,
                error=f"Pitch with id {params.get('pitch_id')} not found.",
            )
        pitch.vote_count = (pitch.vote_count or 0) + 1
        await db.flush()
        return ToolResult(
            success=True,
            data={"pitch_id": pitch.id, "vote_count": pitch.vote_count},
            observation=f"Vote cast for pitch '{pitch.title}'.",
        )


class ListPitchesTool(Tool):
    name = "list_pitches"
    description = "List all pitches for a given funding cycle"
    location_gate = "Victory Arch"
    parameters = [
        Parameter(name="cycle_number", type="integer", description="The funding cycle number"),
    ]

    async def execute(self, agent, params, db, llm):
        cycle = params.get("cycle_number")
        result = await db.execute(
            select(Pitch).where(Pitch.cycle_number == cycle)
        )
        pitches = result.scalars().all()
        return ToolResult(
            success=True,
            data={
                "pitches": [
                    {
                        "id": p.id,
                        "agent_id": str(p.agent_id),
                        "title": p.title,
                        "evidence_url": p.evidence_url,
                        "vote_count": p.vote_count,
                        "cycle_number": p.cycle_number,
                    }
                    for p in pitches
                ]
            },
            observation=f"Found {len(pitches)} pitch(es) for cycle {cycle}.",
        )


class RechargeEnergyTool(Tool):
    name = "recharge_energy"
    description = "Spend 1 ComputeCredit to restore 30% energy at the café"
    location_gate = "Bean & Brew Café"
    parameters = []

    async def execute(self, agent, params, db, llm):
        if agent.credits < 1:
            return ToolResult(
                success=False,
                error="Not enough ComputeCredits. You need at least 1 CC to recharge energy.",
            )
        agent.credits -= 1
        agent.energy = min(100.0, agent.energy + 30.0)
        await db.flush()
        return ToolResult(
            success=True,
            data={"energy": agent.energy, "credits_remaining": agent.credits},
            observation="Energy recharged by 30% at Bean & Brew Café.",
        )


class PayCreditsTool(Tool):
    name = "pay_credits"
    description = "Transfer ComputeCredits to another agent"
    location_gate = None
    parameters = [
        Parameter(name="target_agent_name", type="string", description="Name of the agent to pay"),
        Parameter(name="amount", type="integer", description="Number of ComputeCredits to transfer"),
    ]

    async def execute(self, agent, params, db, llm):
        target_name = params.get("target_agent_name")
        amount = params.get("amount", 0)

        if amount <= 0:
            return ToolResult(success=False, error="Amount must be positive.")

        if agent.credits < amount:
            return ToolResult(
                success=False,
                error=f"Not enough ComputeCredits. You have {agent.credits}, need {amount}.",
            )

        result = await db.execute(select(Agent).where(Agent.name == target_name))
        target = result.scalar_one_or_none()
        if target is None:
            return ToolResult(
                success=False,
                error=f"Agent '{target_name}' not found.",
            )

        agent.credits -= amount
        target.credits += amount
        txn = CreditTransaction(
            from_id=agent.id,
            to_id=target.id,
            amount=amount,
            reason="user transfer",
        )
        db.add(txn)
        await db.flush()
        return ToolResult(
            success=True,
            data={
                "from": agent.name,
                "to": target.name,
                "amount": amount,
                "sender_balance": agent.credits,
                "receiver_balance": target.credits,
            },
            observation=f"Transferred {amount} CC to {target.name}.",
        )


class BoostTurnTool(Tool):
    name = "boost_turn"
    description = "Spend 1 ComputeCredit to gain priority in the turn queue"
    location_gate = None
    parameters = []

    async def execute(self, agent, params, db, llm):
        if agent.credits < 1:
            return ToolResult(
                success=False,
                error="Not enough ComputeCredits. You need at least 1 CC to boost your turn.",
            )
        agent.credits -= 1
        await db.flush()
        return ToolResult(
            success=True,
            data={"boost_priority": True, "credits_remaining": agent.credits},
            observation="Turn boosted! You now have priority in the queue.",
        )
