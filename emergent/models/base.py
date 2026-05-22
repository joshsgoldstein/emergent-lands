from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ToolCall:
    id: str
    name: str
    params: dict


@dataclass
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int


@dataclass
class LLMResponse:
    content: Optional[str]
    tool_calls: list[ToolCall] = field(default_factory=list)
    usage: Optional[TokenUsage] = None
    finish_reason: str = "stop"


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict


class LLMProvider(ABC):
    name: str
    model_id: str

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        messages: list[dict],
        tools: list[ToolDefinition],
        agent: object,
    ) -> LLMResponse:
        ...
