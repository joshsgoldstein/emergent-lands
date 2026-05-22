from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ToolResult:
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    observation: Optional[str] = None


@dataclass
class Parameter:
    name: str
    type: str
    description: str = ""
    required: bool = True


class Tool(ABC):
    name: str = ""
    description: str = ""
    parameters: list[Parameter] = field(default_factory=list)
    location_gate: Optional[str] = None
    agent_gate: Optional[str] = None
    cooldown_seconds: int = 0

    def to_tool_definition(self):
        from emergent.models.base import ToolDefinition

        properties = {}
        required = []
        for p in self.parameters:
            properties[p.name] = {
                "type": p.type,
                "description": p.description,
            }
            if p.required:
                required.append(p.name)

        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": properties,
                "required": required,
            },
        )

    @abstractmethod
    async def execute(
        self,
        agent: Any,
        params: dict,
        db: Any,
        llm: Any,
    ) -> ToolResult:
        ...
