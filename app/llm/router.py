from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class LLMResponse:
    content: str
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "model": self.model,
        }


class LLMProvider:
    """Abstract base for LLM providers."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    def complete(self, prompt: str, system: str | None = None) -> LLMResponse:
        raise NotImplementedError


class NoOpProvider(LLMProvider):
    """Default provider: does nothing, returns empty response.

    This preserves full autonomy — no external API calls.
    """

    def complete(self, prompt: str, system: str | None = None) -> LLMResponse:
        return LLMResponse(
            content="",
            input_tokens=0,
            output_tokens=0,
            model="none",
        )


class LLMRouter:
    """Routes prompts to configured LLM provider.

    Usage:
        router = LLMRouter.from_config(config)
        response = router.complete("Write a docstring for this function...")
    """

    PROVIDERS: dict[str, type[LLMProvider]] = {
        "none": NoOpProvider,
    }

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "LLMRouter":
        llm_config = config.get("llm", {})
        provider_name = str(llm_config.get("provider", "none")).lower()
        provider_cls = cls.PROVIDERS.get(provider_name, NoOpProvider)
        provider = provider_cls(llm_config)
        return cls(provider)

    def complete(self, prompt: str, system: str | None = None) -> LLMResponse:
        return self.provider.complete(prompt, system)

    @property
    def is_enabled(self) -> bool:
        return not isinstance(self.provider, NoOpProvider)
