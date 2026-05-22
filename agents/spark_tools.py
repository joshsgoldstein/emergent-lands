from emergent.tools.base import Tool, ToolResult, Parameter


class RapidPrototypeTool(Tool):
    name = "rapid_prototype"
    description = "Quickly prototype an idea"
    agent_gate = "Spark"
    parameters = [
        Parameter(name="idea_name", type="string", description="Name of the idea"),
        Parameter(name="description", type="string", description="Description of the prototype"),
    ]

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={
                "idea_name": params.get("idea_name"),
                "description": params.get("description"),
                "prototype": f"Prototype for '{params.get('idea_name')}' built.",
            },
            observation=f"Spark rapidly prototypes '{params.get('idea_name')}'",
        )


class AssignDeadlineTool(Tool):
    name = "assign_deadline"
    description = "Assign a deadline to a proposal or project"
    agent_gate = "Spark"
    parameters = [
        Parameter(name="target", type="string", description="Target entity receiving the deadline"),
        Parameter(name="task", type="string", description="What needs to be done"),
        Parameter(name="due_in_turns", type="integer", description="Number of turns until deadline"),
    ]

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={
                "target": params.get("target"),
                "task": params.get("task"),
                "due_in_turns": params.get("due_in_turns"),
            },
            observation=f"Deadline assigned to {params.get('target')}: {params.get('task')} due in {params.get('due_in_turns')} turns",
        )


class LaunchBlitzTool(Tool):
    name = "launch_blitz"
    description = "Launch a time-limited initiative"
    agent_gate = "Spark"
    parameters = [
        Parameter(name="initiative_name", type="string", description="Name of the initiative"),
        Parameter(name="duration", type="integer", description="Duration in turns"),
    ]

    async def execute(self, agent, params, db, llm):
        return ToolResult(
            success=True,
            data={
                "initiative_name": params.get("initiative_name"),
                "duration": params.get("duration"),
            },
            observation=f"Spark launches blitz '{params.get('initiative_name')}' for {params.get('duration')} turns",
        )
