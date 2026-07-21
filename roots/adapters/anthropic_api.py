"""Direct Anthropic Messages API adapter (CLI mode)."""

from __future__ import annotations

import os

import httpx

from .base import AdapterError, LLMAdapter, LLMResponse

_API_URL = "https://api.anthropic.com/v1/messages"
_VERSION = "2023-06-01"


class AnthropicAdapter(LLMAdapter):
    name = "anthropic"

    def __init__(
        self,
        model: str = "claude-sonnet-5",
        max_tokens: int = 4096,
        api_key: str | None = None,
        timeout: float = 120.0,
    ) -> None:
        self.model = model
        self.max_tokens = max_tokens
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.timeout = timeout

    async def send(self, prompt: str, tools: list[str] | None = None) -> LLMResponse:
        if not self.api_key:
            raise AdapterError(
                "ANTHROPIC_API_KEY is not set. Export it, or set a different "
                "backend in .roots/config.yaml."
            )
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": _VERSION,
            "content-type": "application/json",
        }
        body = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(_API_URL, headers=headers, json=body)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as e:
            raise AdapterError(
                f"Anthropic API {e.response.status_code}: {e.response.text}"
            ) from e
        except httpx.HTTPError as e:
            raise AdapterError(f"Anthropic API request failed: {e}") from e
        text = "".join(
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text"
        )
        return LLMResponse(text=text, raw=data)
