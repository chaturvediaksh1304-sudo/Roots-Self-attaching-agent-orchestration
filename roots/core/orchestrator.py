"""The Phase 1 loop: grill -> decompose -> generate -> dispatch -> synthesize
-> write memory -> archive run.

Never imports a model SDK — receives an already-built LLMAdapter (Rules.md).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from ..adapters.base import LLMAdapter
from ..memory import store
from ..memory.schema import MemoryState, SubagentOutcome
from . import decomposer, dispatcher, grill, subagent_gen, synthesizer


@dataclass
class RunResult:
    result_path: Path
    memory_path: Path
    history_path: Path
    outcomes: list[dispatcher.SubagentResult]


def _slug(goal: str) -> str:
    import re

    s = re.sub(r"[^a-z0-9]+", "-", goal.lower()).strip("-")
    return (s[:40] or "run").rstrip("-")


async def run(
    goal: str,
    project_root: Path,
    adapter: LLMAdapter,
    asker: grill.Asker,
    on_progress=lambda msg: None,
    timeout: float = 120.0,
) -> RunResult:
    roots_dir = project_root / ".roots"
    roots_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    on_progress("Grilling to clarify the goal")
    answers = await grill.grill(goal, adapter, asker)
    context = (
        "\n".join(f"{q} -> {a}" for q, a in answers.items()) or "(none)"
    )

    on_progress("Decomposing into subtasks")
    decomp = await decomposer.decompose(goal, context, adapter)
    (roots_dir / "decomposition.json").write_text(
        json.dumps(
            {"goal": goal, "subtasks": [asdict(s) for s in decomp.subtasks]},
            indent=2,
        )
    )
    on_progress(f"Decomposed into {len(decomp.subtasks)} subtask(s)")

    on_progress("Generating subagent configs")
    config_paths = subagent_gen.generate(project_root, decomp.subtasks)

    layers = dispatcher.plan_layers(decomp.subtasks)
    total = len(decomp.subtasks)
    for i, name in enumerate([n for layer in layers for n in layer], 1):
        boundary = next(s.boundary for s in decomp.subtasks if s.name == name)
        on_progress(f"[{i}/{total}] Dispatching subagent: {name} - {boundary}")
    outcomes = await dispatcher.dispatch(decomp, adapter, config_paths, timeout)

    on_progress("Synthesizing final result")
    result_path = synthesizer.synthesize(
        goal, timestamp, outcomes, roots_dir / "result.md"
    )

    memory = MemoryState(
        goal=goal,
        timestamp=timestamp,
        status="complete" if all(o.status == "ok" for o in outcomes) else "partial",
        plan=[f"{s.name}: {s.boundary}" for s in decomp.subtasks],
        outcomes=[
            SubagentOutcome(
                name=o.name, status=o.status, summary=o.summary,
                result_path=o.result_path,
            )
            for o in outcomes
        ],
        next_step="Phase 1 run complete.",
    )
    memory_path = store.write_memory(project_root, memory)

    history_path = store.archive_run(project_root, _slug(goal), timestamp)
    on_progress(f"Archived run to {history_path}")

    return RunResult(result_path, memory_path, history_path, outcomes)
