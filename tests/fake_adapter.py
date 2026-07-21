"""Deterministic in-memory adapter for offline tests (no network, no tokens)."""

from __future__ import annotations

import asyncio
from typing import Callable

from roots.adapters.base import LLMAdapter, LLMResponse


class FakeAdapter(LLMAdapter):
    name = "fake"

    def __init__(
        self,
        responses: list[str] | None = None,
        handler: Callable[[str], str] | None = None,
        delay: float = 0.0,
    ) -> None:
        # Either a fixed queue of replies (consumed in order) or a handler that
        # computes a reply from the prompt. `delay` lets async tests observe
        # concurrency.
        self._responses = list(responses or [])
        self._handler = handler
        self.delay = delay
        self.calls: list[str] = []

    async def send(self, prompt: str, tools: list[str] | None = None) -> LLMResponse:
        self.calls.append(prompt)
        if self.delay:
            await asyncio.sleep(self.delay)
        if self._handler is not None:
            return LLMResponse(text=self._handler(prompt))
        if self._responses:
            return LLMResponse(text=self._responses.pop(0))
        return LLMResponse(text="")
