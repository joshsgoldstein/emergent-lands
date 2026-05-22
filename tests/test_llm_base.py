import inspect
import pytest
from dataclasses import dataclass
from emergent.models.base import (
    LLMResponse,
    ToolCall,
    TokenUsage,
    LLMProvider,
)


def test_tool_call_dataclass():
    tc = ToolCall(id="call_123", name="go_to_place", params={"place": "Town Hall"})
    assert tc.id == "call_123"
    assert tc.name == "go_to_place"
    assert tc.params == {"place": "Town Hall"}


def test_token_usage_dataclass():
    tu = TokenUsage(prompt_tokens=100, completion_tokens=50)
    assert tu.prompt_tokens == 100
    assert tu.completion_tokens == 50


def test_llm_response_creation():
    tc = ToolCall(id="call_1", name="say", params={"message": "hello"})
    tu = TokenUsage(prompt_tokens=50, completion_tokens=10)
    resp = LLMResponse(
        content="Hello there!",
        tool_calls=[tc],
        usage=tu,
        finish_reason="tool_use",
    )
    assert resp.content == "Hello there!"
    assert len(resp.tool_calls) == 1
    assert resp.finish_reason == "tool_use"


def test_llm_provider_is_abstract():
    assert inspect.isabstract(LLMProvider)


def test_llm_provider_has_abstract_generate():
    assert "generate" in LLMProvider.__abstractmethods__


class FakeProvider(LLMProvider):
    name = "fake"
    model_id = "fake-model"

    async def generate(self, system_prompt, messages, tools, agent):
        return LLMResponse(
            content="ok",
            tool_calls=[],
            usage=TokenUsage(prompt_tokens=0, completion_tokens=0),
            finish_reason="stop",
        )


@pytest.mark.asyncio
async def test_fake_provider_works():
    provider = FakeProvider()
    resp = await provider.generate(
        system_prompt="You are a test agent.",
        messages=[],
        tools=[],
        agent=None,
    )
    assert resp.content == "ok"
    assert resp.finish_reason == "stop"
