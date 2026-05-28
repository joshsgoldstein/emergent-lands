import asyncio
import json
from typing import Optional

from openai import OpenAI
from openai.types.chat import ChatCompletionToolParam

from emergent.models.base import (
    LLMProvider,
    LLMResponse,
    ToolCall,
    ToolDefinition,
    TokenUsage,
)


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-5-mini",
        base_url: Optional[str] = None,
    ):
        self.model_id = model
        self._client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            max_retries=0,
            timeout=120,
        )
        self._loop = None

    def _to_openai_tools(
        self, tools: list[ToolDefinition]
    ) -> list[ChatCompletionToolParam]:
        return [
            ChatCompletionToolParam(
                type="function",
                function={
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            )
            for t in tools
        ]

    async def generate(
        self,
        system_prompt: str,
        messages: list[dict],
        tools: list[ToolDefinition],
        agent: object,
    ) -> LLMResponse:
        openai_tools = self._to_openai_tools(tools) if tools else None
        prompt_messages = [{"role": "system", "content": system_prompt}]
        if not messages:
            prompt_messages.append(
                {"role": "user", "content": "What do you do in this moment?"}
            )
        else:
            prompt_messages.extend(messages)
        response = await asyncio.to_thread(
            self._client.chat.completions.create,
            model=self.model_id,
            messages=prompt_messages,
            tools=openai_tools or None,
            max_tokens=512,
        )
        choice = response.choices[0]
        msg = choice.message
        tool_calls = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        params=json.loads(tc.function.arguments),
                    )
                )
        usage = None
        if response.usage:
            usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
            )
        return LLMResponse(
            content=msg.content,
            tool_calls=tool_calls,
            usage=usage,
            finish_reason=str(choice.finish_reason) if choice.finish_reason else "stop",
        )
