"""Model-agnostic adapter interface.

Hard rule (Rules.md): everything in roots/core/ depends only on `LLMAdapter`.
No core module may import a concrete model SDK. This is what makes Roots
model-agnostic rather than Claude-specific.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class LLMResponse:
    text: str
    raw: dict[str, Any] | None = None


class AdapterError(RuntimeError):
    """Real backend failure (network, auth, rate limit). Surface it — never
    swallow it and return a fabricated result (Rules.md, error handling)."""


class LLMAdapter(ABC):
    name: str = "base"

    @abstractmethod
    async def send(self, prompt: str, tools: list[str] | None = None) -> LLMResponse:
        """Send a single prompt, return the model's text. `tools` is the
        subagent's tool allowlist; Phase 1 adapters record it but do not yet
        translate it into provider-native tool-use.
        # ponytail: Phase 1 subagents are text-generation; wire real tool-use
        # in Phase 2+ when self-repair needs to observe tool failures.
        """


def load_adapter(name: str, **kwargs: Any) -> LLMAdapter:
    """Build an adapter by config name. Lazy imports keep this module free of
    concrete-SDK dependencies (so importing base.py never pulls in httpx)."""
    if name == "anthropic":
        from .anthropic_api import AnthropicAdapter

        return AnthropicAdapter(**kwargs)
    if name == "generic_openai":
        from .generic_openai import GenericOpenAIAdapter

        return GenericOpenAIAdapter(**kwargs)
    if name == "claude_code":
        from .claude_code import ClaudeCodeAdapter

        return ClaudeCodeAdapter(**kwargs)
    raise ValueError(
        f"unknown backend '{name}'. Known: anthropic, generic_openai, claude_code"
    )
