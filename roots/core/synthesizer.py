"""Merge subagent result files into one final result.

Receives only structured summaries + file references (never raw reasoning
traces) — the orchestrator's context stays small regardless of how much work
the subagents did (Architecture.md, "game of telephone" lesson). The final
result.md separates a short summary block from full detail by a horizontal
rule (Design.md).
"""

from __future__ import annotations

from pathlib import Path

from .dispatcher import SubagentResult


def synthesize(
    goal: str, timestamp: str, results: list[SubagentResult], out_path: Path
) -> Path:
    ok = [r for r in results if r.status == "ok"]
    failed = [r for r in results if r.status != "ok"]
    status = "complete" if not failed else "partial"

    lines = [
        "---",
        f"goal: {goal}",
        f"timestamp: {timestamp}",
        f"status: {status}",
        "---",
        "",
        "# Result",
        "",
        "## Summary",
        "",
    ]
    for r in ok:
        lines.append(f"- {r.name}: {r.summary}")
    if failed:
        lines.append("")
        lines.append("### Failed subagents")
        for r in failed:
            lines.append(f"- {r.name}: {r.summary}")

    lines += ["", "---", "", "## Full detail", ""]
    for r in results:
        lines.append(f"### {r.name} ({r.status})")
        lines.append(f"See `{r.result_path}`")
        lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))
    return out_path
