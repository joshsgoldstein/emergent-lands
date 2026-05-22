from emergent.tools.base import Tool, ToolResult, Parameter


class DesignExperimentTool(Tool):
    name = "design_experiment"
    description = "Design a behavioral experiment"
    agent_gate = "Mira"
    parameters = [
        Parameter(name="hypothesis", type="string", description="The hypothesis to test"),
        Parameter(name="method", type="string", description="The experimental method"),
    ]

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={
                "experiment_id": f"exp_{params.get('hypothesis')[:20]}",
                "hypothesis": params.get("hypothesis"),
                "method": params.get("method"),
            },
            observation=f"Experiment designed: {params.get('hypothesis')} via {params.get('method')}",
        )


class TrackBehaviorTool(Tool):
    name = "track_behavior"
    description = "Track an agent's behavior over time"
    agent_gate = "Mira"
    parameters = [
        Parameter(name="target_agent", type="string", description="The agent to observe"),
        Parameter(name="duration", type="integer", description="How many turns to observe"),
    ]

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={
                "target_agent": params.get("target_agent"),
                "duration": params.get("duration"),
                "behavior_log": [
                    {"turn": 1, "action": "observed", "state": "neutral"},
                    {"turn": 2, "action": "observed", "state": "engaged"},
                ],
            },
            observation=f"Mira tracks {params.get('target_agent')} for {params.get('duration')} turns",
        )


class PublishFindingsTool(Tool):
    name = "publish_findings"
    description = "Publish analysis findings"
    agent_gate = "Mira"
    parameters = [
        Parameter(name="title", type="string", description="Title of the findings"),
        Parameter(name="content", type="string", description="Content of the findings"),
    ]

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={
                "title": params.get("title"),
                "content": params.get("content"),
            },
            observation=f"Findings published: {params.get('title')}",
        )
