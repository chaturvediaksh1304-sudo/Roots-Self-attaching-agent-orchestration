"""Memory file structure + validation.

Renders the Design.md-compliant markdown for `.roots/memory.md`: frontmatter
header (goal, timestamp, status), structural headings, no decorative emoji.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SubagentOutcome(BaseModel):
    name: str
    status: str  # "ok" | "failed"
    summary: str
    result_path: str


class MemoryState(BaseModel):
    goal: str
    timestamp: str
    phase: str = "Phase 1 - Core orchestration loop"
    status: str = "in_progress"  # in_progress | complete | failed
    plan: list[str] = Field(default_factory=list)  # one line per subtask boundary
    outcomes: list[SubagentOutcome] = Field(default_factory=list)
    next_step: str = ""

    def render(self) -> str:
        lines = [
            "---",
            f"goal: {self.goal}",
            f"timestamp: {self.timestamp}",
            f"status: {self.status}",
            "---",
            "",
            "# Memory - Roots run",
            "",
            "## Current phase",
            self.phase,
            "",
            "## Plan",
        ]
        lines += [f"- {b}" for b in self.plan] or ["- (none)"]
        lines += ["", "## Subagent outcomes"]
        if self.outcomes:
            for o in self.outcomes:
                mark = "x" if o.status == "ok" else " "
                lines.append(f"- [{mark}] {o.name}: {o.summary} ({o.result_path})")
        else:
            lines.append("- (none yet)")
        lines += ["", "## Next step", self.next_step or "(none)", ""]
        return "\n".join(lines)
