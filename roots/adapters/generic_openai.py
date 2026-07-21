"""OpenAI-compatible endpoint adapter (model-agnostic support).

Works against any /chat/completions endpoint: OpenAI, local llama.cpp servers,
vLLM, OpenRouter, etc. Configured via OPENAI_BASE_URL / OPENAI_API_KEY.
"""

from __future__ import annotations

import os

import httpx

from .base import AdapterError, LLMAdapter, LLMResponse


class GenericOpenAIAdapter(LLMAdapter):
    name = "generic_openai"

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        base_url: str | None = None,
        api_key: str | None = None,
        max_tokens: int = 4096,
        timeout: float = 120.0,
    ) -> None:
        self.model = model
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL")
                         or "https://api.openai.com/v1").rstrip("/")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.max_tokens = max_tokens
        self.timeout = timeout

    async def send(self, prompt: str, tools: list[str] | None = None) -> LLMResponse:
        if not self.api_key:
            raise AdapterError(
                "OPENAI_API_KEY is not set. Export it, or set a different "
                "backend in .roots/config.yaml."
            )
        headers = {
            "authorization": f"Bearer {self.api_key}",
            "content-type": "application/json",
        }
        body = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions", headers=headers, json=body
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as e:
            raise AdapterError(
                f"OpenAI-compatible API {e.response.status_code}: {e.response.text}"
            ) from e
        except httpx.HTTPError as e:
            raise AdapterError(f"OpenAI-compatible API request failed: {e}") from e
        text = data["choices"][0]["message"]["content"]
        return LLMResponse(text=text, raw=data)
