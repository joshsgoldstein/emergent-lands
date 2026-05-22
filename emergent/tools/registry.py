from emergent.tools.base import Tool


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def get_available(self, agent) -> list[Tool]:
        return [
            t
            for t in self._tools.values()
            if (t.agent_gate is None or t.agent_gate == agent.name)
            and (t.location_gate is None or t.location_gate == agent.current_location)
        ]

    def get_available_as_definitions(self, agent):
        return [t.to_tool_definition() for t in self.get_available(agent)]

    @property
    def all_tools(self) -> list[Tool]:
        return list(self._tools.values())

    def __len__(self):
        return len(self._tools)
