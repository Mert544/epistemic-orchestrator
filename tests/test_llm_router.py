from app.llm.router import LLMRouter, NoOpProvider


def test_noop_provider_returns_empty_response():
    provider = NoOpProvider({})
    resp = provider.complete("hello")
    assert resp.content == ""
    assert resp.input_tokens == 0
    assert resp.output_tokens == 0
    assert resp.model == "none"


def test_router_from_config_defaults_to_none():
    config = {}
    router = LLMRouter.from_config(config)
    assert router.is_enabled is False
    resp = router.complete("hello")
    assert resp.content == ""


def test_unknown_provider_fallbacks_to_none():
    config = {"llm": {"provider": "unknown"}}
    router = LLMRouter.from_config(config)
    assert router.is_enabled is False
    resp = router.complete("hello")
    assert resp.content == ""


def test_llm_response_to_dict():
    from app.llm.router import LLMResponse
    resp = LLMResponse(content="hi", input_tokens=5, output_tokens=3, model="none")
    d = resp.to_dict()
    assert d["content"] == "hi"
    assert d["input_tokens"] == 5
    assert d["output_tokens"] == 3
