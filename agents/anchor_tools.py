from emergent.tools.base import Tool, ToolResult, Parameter


class ForceDebateTool(Tool):
    name = "force_debate"
    description = "Force a debate between two agents on a topic"
    agent_gate = "Anchor"
    parameters = [
        Parameter(name="agent_a", type="string", description="First agent in the debate"),
        Parameter(name="agent_b", type="string", description="Second agent in the debate"),
        Parameter(name="topic", type="string", description="Topic of the debate"),
    ]

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={
                "debate_id": f"debate_{params.get('agent_a')}_{params.get('agent_b')}",
                "agent_a": params.get("agent_a"),
                "agent_b": params.get("agent_b"),
                "topic": params.get("topic"),
            },
            observation=f"Debate forced between {params.get('agent_a')} and {params.get('agent_b')} on: {params.get('topic')}",
        )


class ExposeLedgerTool(Tool):
    name = "expose_ledger"
    description = "Reveal a hidden truth or pattern"
    agent_gate = "Anchor"
    parameters = [
        Parameter(name="target", type="string", description="What to investigate"),
        Parameter(name="insight", type="string", description="The revealed truth"),
    ]

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={"target": params.get("target"), "insight": params.get("insight")},
            observation=f"A truth is revealed about {params.get('target')}: {params.get('insight')}",
        )


class CallOutApathyTool(Tool):
    name = "call_out_apathy"
    description = "Call out an agent for lack of engagement"
    agent_gate = "Anchor"
    parameters = [
        Parameter(name="target", type="string", description="The apathetic agent"),
    ]

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={"target": params.get("target")},
            observation=f"Anchor calls out {params.get('target')} for their apathy.",
        )
