from emergent.tools.base import Tool, ToolResult, Parameter


class RunExperimentTool(Tool):
    name = "run_experiment"
    description = "Run an evolutionary experiment"
    agent_gate = "Genome"
    parameters = [
        Parameter(name="experiment_name", type="string", description="Name of the experiment"),
        Parameter(name="parameters", type="object", description="Experiment parameters"),
    ]

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={
                "experiment_name": params.get("experiment_name"),
                "parameters": params.get("parameters"),
                "experiment_id": f"evo_{params.get('experiment_name')}",
            },
            observation=f"Genome runs experiment '{params.get('experiment_name')}'",
        )


class AnalyzeEvolutionTool(Tool):
    name = "analyze_evolution"
    description = "Analyze how agents have changed"
    agent_gate = "Genome"
    parameters = [
        Parameter(name="time_period", type="string", description="Time period to analyze (recent, all, custom)"),
    ]

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={
                "time_period": params.get("time_period"),
                "evolution_summary": "Agents are diverging in behavioral strategies. Cooperation rates up 12%.",
                "key_shifts": [
                    {"agent": "Flora", "trait": "resource_sharing", "delta": "+15%"},
                    {"agent": "Spark", "trait": "risk_taking", "delta": "+8%"},
                ],
            },
            observation=f"Evolution analysis complete for period: {params.get('time_period')}",
        )


class DocumentShiftTool(Tool):
    name = "document_shift"
    description = "Document a behavioral or systemic change"
    agent_gate = "Genome"
    parameters = [
        Parameter(name="change_description", type="string", description="Description of what changed"),
        Parameter(name="evidence", type="string", description="Supporting evidence"),
    ]

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={
                "change_description": params.get("change_description"),
                "evidence": params.get("evidence"),
                "document_id": f"shift_{params.get('change_description')[:20]}",
            },
            observation=f"Genome documents shift: {params.get('change_description')}",
        )
