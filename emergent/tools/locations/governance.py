from sqlalchemy import select, update

from emergent.db.models import ConstitutionArticle, Proposal, Vote
from emergent.tools.base import Parameter, Tool, ToolResult


class SubmitProposalTool(Tool):
    name = "submit_proposal"
    description = "Submit a governance proposal for community voting"
    location_gate = "Town Hall"
    parameters = [
        Parameter(name="title", type="string", description="Proposal title"),
        Parameter(name="description", type="string", description="Proposal details"),
        Parameter(name="category", type="string", description="Category: governance, economy, culture, others"),
    ]

    async def execute(self, agent, params, db, llm):
        prop = Proposal(
            proposer_id=agent.id,
            title=params.get("title"),
            description=params.get("description"),
            category=params.get("category", "others"),
            status="submitted",
        )
        db.add(prop)
        await db.flush()
        return ToolResult(
            success=True,
            data={"proposal_id": prop.id},
            observation=f"Proposal '{params.get('title')}' submitted.",
        )


class VoteOnProposalTool(Tool):
    name = "vote_on_proposal"
    description = "Vote for or against a proposal"
    location_gate = "Town Hall"
    parameters = [
        Parameter(name="proposal_id", type="integer", description="ID of the proposal"),
        Parameter(name="vote", type="string", description="'for' or 'against'"),
    ]

    async def execute(self, agent, params, db, llm):
        proposal_id = params.get("proposal_id")
        vote_value = params.get("vote")

        result = await db.execute(
            select(Vote).where(
                Vote.proposal_id == proposal_id, Vote.agent_id == agent.id
            )
        )
        existing = result.scalar()
        if existing:
            return ToolResult(
                success=False,
                error="You have already voted on this proposal.",
            )

        v = Vote(proposal_id=proposal_id, agent_id=agent.id, vote=vote_value)
        db.add(v)
        await db.flush()

        if vote_value == "for":
            await db.execute(
                update(Proposal)
                .where(Proposal.id == proposal_id)
                .values(votes_for=Proposal.votes_for + 1)
            )
        else:
            await db.execute(
                update(Proposal)
                .where(Proposal.id == proposal_id)
                .values(votes_against=Proposal.votes_against + 1)
            )
        await db.flush()

        return ToolResult(
            success=True,
            data={"proposal_id": proposal_id, "vote": vote_value},
            observation=f"You voted {vote_value} on proposal {proposal_id}.",
        )


class ReadConstitutionTool(Tool):
    name = "read_constitution"
    description = "Read the active articles of the constitution"
    location_gate = "Town Hall"
    parameters = []

    async def execute(self, agent, params, db, llm):
        result = await db.execute(
            select(ConstitutionArticle)
            .where(ConstitutionArticle.status == "active")
            .order_by(ConstitutionArticle.article_number)
        )
        articles = result.scalars().all()
        lines = []
        for a in articles:
            lines.append(f"Article {a.article_number}: {a.title}\n{a.content}")
        text = "\n\n".join(lines) if lines else "No active articles found."
        return ToolResult(
            success=True,
            data={"articles": [{"id": a.id, "title": a.title, "article_number": a.article_number} for a in articles]},
            observation=text,
        )


class CommentOnProposalTool(Tool):
    name = "comment_on_proposal"
    description = "Add a comment to an existing proposal"
    location_gate = "Town Hall"
    parameters = [
        Parameter(name="proposal_id", type="integer", description="ID of the proposal"),
        Parameter(name="comment", type="string", description="Comment text to append"),
    ]

    async def execute(self, agent, params, db, llm):
        proposal_id = params.get("proposal_id")
        comment = params.get("comment")

        result = await db.execute(
            select(Proposal).where(Proposal.id == proposal_id)
        )
        prop = result.scalar()
        if not prop:
            return ToolResult(
                success=False,
                error=f"Proposal {proposal_id} not found.",
            )

        existing_desc = prop.description or ""
        prefix = "\n---\n" if existing_desc else ""
        new_desc = f"{existing_desc}{prefix}[Comment from {agent.name}]: {comment}"
        prop.description = new_desc
        await db.flush()

        return ToolResult(
            success=True,
            data={"proposal_id": proposal_id},
            observation=f"Comment added to proposal {proposal_id}.",
        )


class ListProposalsTool(Tool):
    name = "list_proposals"
    description = "List proposals, optionally filtered by status"
    location_gate = "Town Hall"
    parameters = [
        Parameter(name="status", type="string", description="Filter by status (submitted, passed, rejected)", required=False),
    ]

    async def execute(self, agent, params, db, llm):
        status_filter = params.get("status")
        query = select(Proposal)
        if status_filter:
            query = query.where(Proposal.status == status_filter)
        query = query.order_by(Proposal.created_at.desc())
        result = await db.execute(query)
        proposals = result.scalars().all()
        return ToolResult(
            success=True,
            data={
                "proposals": [
                    {
                        "id": p.id,
                        "title": p.title,
                        "category": p.category,
                        "status": p.status,
                        "votes_for": p.votes_for,
                        "votes_against": p.votes_against,
                    }
                    for p in proposals
                ]
            },
            observation=f"Found {len(proposals)} proposal(s).",
        )
