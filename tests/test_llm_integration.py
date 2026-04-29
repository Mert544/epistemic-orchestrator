from unittest.mock import MagicMock, patch

import pytest

from app.llm.router import LLMRouter, NoOpProvider, LLMProvider


def test_noop_provider_never_calls_api():
    """Ensure default provider makes zero external calls."""
    provider = NoOpProvider({})
    resp = provider.complete("anything")
    assert resp.content == ""
    assert resp.input_tokens == 0
    assert resp.output_tokens == 0


def test_router_with_noop_provider():
    """Integration-level: router delegates to noop provider."""
    config = {"llm": {"provider": "none"}}
    router = LLMRouter.from_config(config)
    assert router.is_enabled is False

    resp = router.complete("prompt")
    assert resp.content == ""


def test_llm_provider_base_class():
    """Base provider class raises NotImplementedError as expected."""
    provider = LLMProvider({})
    with pytest.raises(NotImplementedError):
        provider.complete("test")
