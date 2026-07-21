"""Execute subagents: parallel where independent, sequential where dependent.

`plan_layers` is a pure topological layering (tested in tests/test_dispatcher.py)
— subtasks in the same layer have no dependency between them and run
concurrently via asyncio.gather; layers run in order. The dispatcher never
silently serializes independent work nor parallelizes dependent work (Rules.md).

Every dispatch handles timeout, malformed output, and tool/adapter failure; a
failed subagent is logged to its own result file with a reason, never silent.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

from ..adapters.base import AdapterError, LLMAdapter
from .decomposer import Decomposition, Subtask

RESULTS_REL = Path(".roots/agents")  # result files sit beside their configs


@dataclass
class SubagentResult:
    name: str
    status: str  # "ok" | "failed"
    summary: str
    result_path: str


class DependencyError(ValueError):
    """Unresolvable or cyclic dependency graph."""


def plan_layers(subtasks: list[Subtask]) -> list[list[str]]:
    """Group subtask names into dependency layers (Kahn's algorithm).
    Layer 0 has no deps; each later layer depends only on earlier ones.
    Raises DependencyError on an unknown dep or a cycle."""
    names = {s.name for s in subtasks}
    remaining = {s.name: set(s.depends_on) for s in subtasks}
    for name, deps in remaining.items():
        unknown = deps - names
        if unknown:
            raise DependencyError(f"{name} depends on unknown {sorted(unknown)}")

    layers: list[list[str]] = []
    done: set[str] = set()
    while remaining:
        ready = sorted(n for n, deps in remaining.items() if deps <= done)
        if not ready:
            raise DependencyError(f"dependency cycle among {sorted(remaining)}")
        layers.append(ready)
        done |= set(ready)
        for n in ready:
            del remaining[n]
    return layers


def _parse_summary(text: str) -> str:
    for line in text.splitlines():
        if line.strip().upper().startswith("SUMMARY:"):
            return line.split(":", 1)[1].strip()
    # Fallback: first non-empty line.
    for line in text.splitlines():
        if line.strip():
            return line.strip()[:200]
    return "(empty output)"


def _build_prompt(config_text: str) -> str:
    return (
        "You are a specialized subagent. Execute your task per this config, "
        "honoring the output contract exactly.\n\n" + config_text
    )


async def _run_one(
    subtask: Subtask,
    config_path: Path,
    adapter: LLMAdapter,
    timeout: float,
) -> SubagentResult:
    result_path = config_path.with_name(f"{subtask.name}.result.md")
    header = (
        f"---\nrole: {subtask.name}\nboundary: {subtask.boundary}\n---\n\n"
    )
    try:
        config_text = config_path.read_text()
        resp = await asyncio.wait_for(
            adapter.send(_build_prompt(config_text), tools=subtask.tools),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        reason = f"timed out after {timeout}s"
        result_path.write_text(header + f"# Failed\n\n{reason}\n")
        return SubagentResult(subtask.name, "failed", reason, str(result_path))
    except AdapterError as e:
        reason = f"adapter error: {e}"
        result_path.write_text(header + f"# Failed\n\n{reason}\n")
        return SubagentResult(subtask.name, "failed", reason, str(result_path))

    text = resp.text.strip()
    if not text:
        reason = "malformed output: empty response"
        result_path.write_text(header + f"# Failed\n\n{reason}\n")
        return SubagentResult(subtask.name, "failed", reason, str(result_path))

    summary = _parse_summary(text)
    result_path.write_text(
        header + f"## Summary\n\n{summary}\n\n---\n\n## Full detail\n\n{text}\n"
    )
    return SubagentResult(subtask.name, "ok", summary, str(result_path))


async def dispatch(
    decomposition: Decomposition,
    adapter: LLMAdapter,
    config_paths: dict[str, Path],
    timeout: float = 120.0,
) -> list[SubagentResult]:
    """Run all subagents layer by layer. Within a layer, concurrent; across
    layers, sequential. Returns results in dependency order."""
    by_name = {s.name: s for s in decomposition.subtasks}
    results: list[SubagentResult] = []
    for layer in plan_layers(decomposition.subtasks):
        coros = [
            _run_one(by_name[n], config_paths[n], adapter, timeout) for n in layer
        ]
        results.extend(await asyncio.gather(*coros))
    return results
