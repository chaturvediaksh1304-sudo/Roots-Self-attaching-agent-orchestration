"""Write real subagent config files to disk before dispatch.

Every subagent is a real .md file (Rules.md / Architecture.md) — not an
in-memory object. This is what makes dispatch inspectable and makes Phase 2
self-repair a plain file edit. Configs are generated from the actual
decomposition, never picked from a fixed template library (Rules.md).
"""

from __future__ import annotations

from pathlib import Path

from .decomposer import Subtask

AGENTS_REL = Path(".roots/agents")

# Subagent output convention (Design.md: summary separated from full detail).
_OUTPUT_CONTRACT = (
    "Begin your reply with a single line `SUMMARY: <one sentence>`, then a "
    "blank line, then the full detail. The orchestrator reads only the summary "
    "line; the full detail is written to your result file."
)


def render_config(subtask: Subtask) -> str:
    tools = ", ".join(subtask.tools) if subtask.tools else "(none)"
    deps = ", ".join(subtask.depends_on) if subtask.depends_on else "(none)"
    return "\n".join([
        "---",
        f"role: {subtask.name}",
        f"depends_on: {deps}",
        f"tools: {tools}",
        "---",
        "",
        f"# {subtask.name}",
        "",
        "## Task boundary",
        subtask.boundary,
        "",
        "## Tool allowlist",
        tools,
        "",
        "## Output contract",
        _OUTPUT_CONTRACT,
        "",
    ])


def generate(root: Path, subtasks: list[Subtask]) -> dict[str, Path]:
    """Write one config file per subtask, named `<role>.md` (Design.md).
    Returns {subtask_name: path}."""
    agents_dir = root / AGENTS_REL
    agents_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for st in subtasks:
        path = agents_dir / f"{st.name}.md"
        path.write_text(render_config(st))
        paths[st.name] = path
    return paths
