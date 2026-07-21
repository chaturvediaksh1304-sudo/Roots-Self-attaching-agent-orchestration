# Rules.md — Roots

Boundaries for whatever AI (Claude Code or otherwise) builds this project.

## Language & libraries
- Python 3.11+ only. No mixing in Node/TS for the core package — CLI wrapper is Python too.
- Stdlib + minimal deps. Allowed: `click` or `typer` (pick one, never both), `pyyaml`, `httpx` (for API calls, not `requests`), `pydantic` (for config/schema validation), `pytest` for tests.
- No ORM, no database library in v1. Flat files only. Don't add SQLite "just in case" — only when Phase 3 explicitly needs it and flat-file scan is measured as too slow.
- No web framework of any kind in v1 — there is no UI. If a future dashboard phase happens, that's a new decision, not a default.
- Don't add a dependency for something stdlib already does (e.g. no extra JSON libs, no extra CLI-arg parsers beyond the one chosen framework).

## Architecture boundaries
- Core orchestration logic (`core/`) must never import a specific model SDK directly. All model calls go through `adapters/base.py`'s `LLMAdapter` interface. Violating this breaks model-agnosticism — treat it as a hard rule, not a guideline.
- Subagent definitions are always written to disk as real files before dispatch. No in-memory-only subagent execution — breaks inspectability and self-repair.
- Dispatcher must support both parallel and sequential execution paths explicitly — never silently serialize what should be parallel, never silently parallelize dependent tasks.
- `.roots/history/` is append-only. Nothing in `core/evolution.py` or elsewhere should delete or overwrite past run records.

## Error handling
- Every subagent dispatch must handle: timeout, malformed output, tool failure. On failure, log to that run's `result.md` with a clear failure reason — never fail silently.
- Self-repair (`self_repair.py`) only triggers after a defined failure, never speculatively "improves" a subagent that succeeded. Don't over-engineer — repair on evidence, not vibes.
- CLI must never crash on bad user input during the grill phase — reprompt with a clear message instead.
- If a model adapter call fails (network, auth, rate limit), surface the actual error to the user. Never swallow it and return a fabricated result.

## Agent behavior rules (for the orchestrator itself, at runtime)
- Grill phase: max ~4 questions, one at a time, adapt based on prior answer. Never fire a wall of questions upfront.
- Decomposition: every subtask must have an explicit, non-overlapping boundary. If two subtasks could plausibly do the same work, merge them or redraw the boundary — don't dispatch both.
- Scale subagent count to task complexity. Simple task = 1 subagent. Don't default to spawning multiple subagents for something a single agent handles in a few tool calls.
- Subagent tool access is allowlisted per subagent, minimal to its task. Never grant a subagent every available tool by default.
- Subagent output back to orchestrator: structured summary + reference to full result file. Never pipe full raw reasoning traces back into orchestrator context.

## What the AI building this should NOT do
- Don't build the self-repair loop or evolution engine before the base orchestrator + dispatch + generation loop is working and tested. Sequence matters — see Phases.md.
- Don't add a config/dashboard UI "since it'd be easy" — explicitly out of scope for v1.
- Don't hardcode Anthropic/Claude assumptions into `core/` — that's what the adapter layer is for.
- Don't invent subagent config templates ahead of time — generation must be dynamic, driven by the actual decomposition, not picked from a fixed library (that's a v1 non-goal; static templates are a shortcut that undermines the whole point of the project).
- Don't skip writing tests for `decomposer.py` and `dispatcher.py` — these are the highest-risk-of-silent-failure modules.
