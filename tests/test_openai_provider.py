import pytest
from unittest.mock import MagicMock

from emergent.models.base import ToolDefinition
from emergent.models.openai_provider import OpenAIProvider


def test_provider_has_name_and_model():
    provider = OpenAIProvider(api_key="test-key", model="gpt-5-mini")
    assert provider.name == "openai"
    assert provider.model_id == "gpt-5-mini"


@pytest.mark.asyncio
async def test_generate_returns_normalized_response():
    mock_message = MagicMock()
    mock_message.content = "Hello from GPT"
    mock_message.tool_calls = None
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_choice.finish_reason = "stop"
    mock_usage = MagicMock()
    mock_usage.prompt_tokens = 50
    mock_usage.completion_tokens = 10
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = mock_usage
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    provider = OpenAIProvider(api_key="test-key", model="gpt-5-mini")
    provider._client = mock_client

    resp = await provider.generate(
        system_prompt="You are a test agent.",
        messages=[{"role": "user", "content": "hi"}],
        tools=[
            ToolDefinition(
                name="say",
                description="Say something",
                parameters={
                    "type": "object",
                    "properties": {"message": {"type": "string"}},
                },
            )
        ],
        agent=None,
    )
    assert resp.content == "Hello from GPT"
    assert resp.usage.prompt_tokens == 50
    assert resp.usage.completion_tokens == 10
    assert resp.finish_reason == "stop"
