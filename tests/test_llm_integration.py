from unittest.mock import MagicMock, patch

import pytest

from app.llm.router import LLMRouter, NoOpProvider, OpenAICompatibleProvider


def test_mock_openai_provider_returns_response():
    """Test OpenAI-compatible provider with a mocked client."""
    provider = OpenAICompatibleProvider({
        "api_key": "test-key",
        "model": "gpt-4o-mini",
        "max_tokens": 100,
        "temperature": 0.0,
    })

    # Mock the OpenAI client and response
    mock_choice = MagicMock()
    mock_choice.message.content = "def add(a, b): return a + b"

    mock_usage = MagicMock()
    mock_usage.prompt_tokens = 50
    mock_usage.completion_tokens = 20

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = mock_usage

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    provider._client = mock_client

    resp = provider.complete("Write a simple add function")

    assert resp.content == "def add(a, b): return a + b"
    assert resp.input_tokens == 50
    assert resp.output_tokens == 20
    assert resp.model == "gpt-4o-mini"


def test_mock_openai_provider_with_system_prompt():
    """Test that system prompt is passed correctly."""
    provider = OpenAICompatibleProvider({"api_key": "test", "model": "gpt-4"})

    mock_choice = MagicMock()
    mock_choice.message.content = "ok"
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = None

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    provider._client = mock_client

    provider.complete("hello", system="You are a coding assistant")

    call_args = mock_client.chat.completions.create.call_args
    messages = call_args.kwargs["messages"]
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "You are a coding assistant"
    assert messages[1]["role"] == "user"


def test_router_routes_to_correct_provider():
    """Integration-level: router delegates to correct provider."""
    config = {"llm": {"provider": "openai", "api_key": "x", "model": "gpt-4o-mini"}}
    router = LLMRouter.from_config(config)
    assert router.is_enabled is True

    # Patch the provider's complete method
    with patch.object(router.provider, "complete") as mock_complete:
        mock_complete.return_value = MagicMock(
            content="result", input_tokens=10, output_tokens=5, model="gpt-4o-mini"
        )
        resp = router.complete("prompt")
        assert resp.content == "result"
        mock_complete.assert_called_once_with("prompt", None)


def test_noop_provider_never_calls_api():
    """Ensure default provider makes zero external calls."""
    provider = NoOpProvider({})
    resp = provider.complete("anything")
    assert resp.content == ""
    assert resp.input_tokens == 0
    assert resp.output_tokens == 0


def test_local_provider_uses_different_base_url():
    """Local provider points to localhost/Ollama by default."""
    provider = OpenAICompatibleProvider({
        "api_key": "local",
        "base_url": "http://localhost:11434/v1",
        "model": "llama3",
    })
    # Just verify initialization doesn't fail and base_url is stored
    assert provider.base_url == "http://localhost:11434/v1"
    assert provider.model == "llama3"
