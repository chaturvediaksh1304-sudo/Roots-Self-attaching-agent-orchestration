"""Claude Code Task-tool adapter (plugin mode).

When Roots runs as a Claude Code plugin, subagent dispatch is delegated to
Claude Code's native `Task` tool rather than a direct API call. That tool is
only reachable from inside the Claude Code runtime — there is no import for it
in a standalone Python process.

Phase 1 ships this adapter to the LLMAdapter contract (see
tests/test_adapters.py) so the dispatcher can target it, but real end-to-end
execution is exercised only when Roots is installed and run as a plugin. If a
Task-tool bridge is injected (`task_runner`), send() uses it; otherwise send()
fails loudly instead of silently degrading.
"""

from __future__ import annotations

from typing import Awaitable, Callable

from .base import AdapterError, LLMAdapter, LLMResponse

# A bridge the plugin runtime injects: given a prompt + tool allowlist, it runs
# a Claude Code Task and returns the subagent's text output.
TaskRunner = Callable[[str, list[str] | None], Awaitable[str]]


class ClaudeCodeAdapter(LLMAdapter):
    name = "claude_code"

    def __init__(self, task_runner: TaskRunner | None = None) -> None:
        self.task_runner = task_runner

    async def send(self, prompt: str, tools: list[str] | None = None) -> LLMResponse:
        if self.task_runner is None:
            raise AdapterError(
                "claude_code backend requires the Claude Code plugin runtime. "
                "Run Roots as a plugin, or set backend: anthropic in "
                ".roots/config.yaml for standalone CLI use."
            )
        text = await self.task_runner(prompt, tools)
        return LLMResponse(text=text, raw=None)
