"""Goal -> subtasks with explicit, non-overlapping boundaries.

Highest-risk-of-silent-failure module (Rules.md) — the LLM proposes a
decomposition, but boundary-overlap detection and structural validation are
pure functions, tested independently of any model in tests/test_decomposer.py.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from ..adapters.base import LLMAdapter


@dataclass
class Subtask:
    name: str  # kebab-case role, e.g. "api-research"
    boundary: str  # one explicit sentence
    depends_on: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)


@dataclass
class Decomposition:
    goal: str
    subtasks: list[Subtask]


class DecompositionError(ValueError):
    """Malformed or self-contradictory decomposition (Rules.md: handle
    malformed model output, never fail silently)."""


_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "for", "in", "on", "with",
    "into", "from", "this", "that", "its", "by", "as", "at", "is", "be",
    "write", "create", "build", "make", "generate", "produce", "add", "using",
}


def _tokens(text: str) -> set[str]:
    return {
        w for w in re.findall(r"[a-z0-9]+", text.lower())
        if w not in _STOPWORDS and len(w) > 2
    }


def detect_overlaps(
    subtasks: list[Subtask], threshold: float = 0.5
) -> list[tuple[str, str, float]]:
    """Flag subtask pairs whose boundaries likely do the same work.

    Jaccard similarity over content tokens of the two boundary sentences;
    pairs at or above `threshold` are returned as (name_a, name_b, score).
    # ponytail: naive token-overlap heuristic. Upgrade path if it mis-fires:
    # embed the boundaries or use an LLM judge. Adequate for Phase 1 guarding.
    """
    flagged: list[tuple[str, str, float]] = []
    for i in range(len(subtasks)):
        for j in range(i + 1, len(subtasks)):
            a, b = _tokens(subtasks[i].boundary), _tokens(subtasks[j].boundary)
            if not a or not b:
                continue
            score = len(a & b) / len(a | b)
            if score >= threshold:
                flagged.append((subtasks[i].name, subtasks[j].name, round(score, 2)))
    return flagged


def validate(subtasks: list[Subtask]) -> None:
    """Structural checks: non-empty, unique kebab names, resolvable deps, no
    self-dependency. Raises DecompositionError on any violation."""
    if not subtasks:
        raise DecompositionError("decomposition produced zero subtasks")
    names = [s.name for s in subtasks]
    dupes = {n for n in names if names.count(n) > 1}
    if dupes:
        raise DecompositionError(f"duplicate subtask names: {sorted(dupes)}")
    known = set(names)
    for s in subtasks:
        if not s.name or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", s.name):
            raise DecompositionError(f"subtask name not kebab-case: {s.name!r}")
        if not s.boundary.strip():
            raise DecompositionError(f"subtask {s.name} has empty boundary")
        if s.name in s.depends_on:
            raise DecompositionError(f"subtask {s.name} depends on itself")
        for dep in s.depends_on:
            if dep not in known:
                raise DecompositionError(
                    f"subtask {s.name} depends on unknown '{dep}'"
                )


def _extract_json(text: str) -> object:
    """Pull a JSON value out of a model response, tolerating ```json fences."""
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else text
    try:
        return json.loads(candidate.strip())
    except json.JSONDecodeError as e:
        raise DecompositionError(f"model did not return valid JSON: {e}") from e


def parse(text: str) -> list[Subtask]:
    data = _extract_json(text)
    if not isinstance(data, list):
        raise DecompositionError("expected a JSON array of subtasks")
    subtasks = []
    for item in data:
        if not isinstance(item, dict) or "name" not in item or "boundary" not in item:
            raise DecompositionError(f"malformed subtask entry: {item!r}")
        subtasks.append(
            Subtask(
                name=item["name"],
                boundary=item["boundary"],
                depends_on=list(item.get("depends_on", [])),
                tools=list(item.get("tools", [])),
            )
        )
    return subtasks


_PROMPT = """Decompose this goal into independent subtasks for parallel agents.

Goal: {goal}

Clarifications:
{context}

Rules:
- Prefer the FEWEST subtasks. Default to ONE subtask. Only create a separate
  subtask when it can run in genuine PARALLEL with another OR needs a distinct
  tool set. Do NOT split one job into sequential "define" + "implement" +
  "document" steps that a single agent does in order — that is not parallelism.
- Every subtask boundary must be a single explicit sentence and must NOT
  overlap another subtask's work. If two would do the same thing, merge them.
- Give each subtask a kebab-case role name (e.g. api-research, schema-design).
- List depends_on (names of subtasks that must finish first) and tools (the
  minimal tool allowlist for this subtask).
{overlap_note}
Return ONLY a JSON array, no prose and no markdown fences:
[{{"name": "...", "boundary": "...", "depends_on": [], "tools": []}}]
"""

_JSON_NUDGE = (
    "\nYour previous reply was not valid JSON. Return ONLY a JSON array — "
    "no prose, no explanation, no markdown fences.\n"
)


async def _decode_with_retry(
    prompt: str, adapter: LLMAdapter, attempts: int = 3
) -> list[Subtask]:
    """Send + parse + validate, retrying on malformed output. Model JSON is
    occasionally off (trailing prose, truncation); one bad sample must not kill
    the run. Re-ask with a stricter nudge up to `attempts` times, then surface
    the real error (Rules.md: never fail silently)."""
    last_err: DecompositionError | None = None
    for i in range(attempts):
        resp = await adapter.send(prompt if i == 0 else prompt + _JSON_NUDGE)
        try:
            subtasks = parse(resp.text)
            validate(subtasks)
            return subtasks
        except DecompositionError as e:
            last_err = e
    raise DecompositionError(
        f"decomposition failed after {attempts} attempts: {last_err}"
    )


async def decompose(goal: str, context: str, adapter: LLMAdapter) -> Decomposition:
    """LLM decomposition (with parse-retry) + one bounded repair pass if
    boundaries overlap."""
    base = _PROMPT.format(goal=goal, context=context, overlap_note="")
    subtasks = await _decode_with_retry(base, adapter)

    overlaps = detect_overlaps(subtasks)
    if overlaps:
        note = (
            "\nThe previous attempt had overlapping boundaries between: "
            + "; ".join(f"{a} & {b}" for a, b, _ in overlaps)
            + ". Merge or redraw them so no two subtasks share work.\n"
        )
        repaired = _PROMPT.format(goal=goal, context=context, overlap_note=note)
        subtasks = await _decode_with_retry(repaired, adapter)

    return Decomposition(goal=goal, subtasks=subtasks)
