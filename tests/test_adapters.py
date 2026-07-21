import asyncio

import pytest

from roots.adapters.base import AdapterError, LLMAdapter, load_adapter
from roots.adapters.claude_code import ClaudeCodeAdapter


def test_load_adapter_known_backends():
    assert isinstance(load_adapter("anthropic"), LLMAdapter)
    assert isinstance(load_adapter("generic_openai"), LLMAdapter)
    assert isinstance(load_adapter("claude_code"), LLMAdapter)


def test_load_adapter_unknown_raises():
    with pytest.raises(ValueError):
        load_adapter("nope")


def test_claude_code_without_runner_fails_loudly():
    # Phase 1 contract: standalone claude_code has no Task tool -> clear error,
    # never a silent fabricated result.
    with pytest.raises(AdapterError):
        asyncio.run(ClaudeCodeAdapter().send("hi"))


def test_claude_code_uses_injected_runner():
    async def runner(prompt, tools):
        return f"ran: {prompt}"

    resp = asyncio.run(ClaudeCodeAdapter(task_runner=runner).send("hi", ["Read"]))
    assert resp.text == "ran: hi"
