"""Adaptive grill: clarify the goal one question at a time (max ~4).

The engine is model-driven but I/O-agnostic — it takes an `asker` callable so
the CLI can drive it with styled prompts and tests can drive it with a script.
Never fires a wall of questions upfront (Rules.md / Design.md).
"""

from __future__ import annotations

from typing import Callable

from ..adapters.base import LLMAdapter

# asker(question, index, total) -> user's answer. Sync: the CLI blocks on input.
Asker = Callable[[str, int, int], str]

_STOP = "DONE"

_PROMPT = """You are clarifying a project goal before decomposing it into subtasks.

Goal: {goal}

Answers so far:
{answers}

Ask the SINGLE most useful next question to resolve scope, output format, or
constraints. One question only, no preamble. If the goal, scope, output format,
and constraints are already clear enough to decompose, reply with exactly: {stop}
"""


def _format_answers(answers: dict[str, str]) -> str:
    if not answers:
        return "(none yet)"
    return "\n".join(f"Q: {q}\nA: {a}" for q, a in answers.items())


async def grill(
    goal: str,
    adapter: LLMAdapter,
    asker: Asker,
    max_questions: int = 4,
) -> dict[str, str]:
    answers: dict[str, str] = {}
    for i in range(1, max_questions + 1):
        prompt = _PROMPT.format(
            goal=goal, answers=_format_answers(answers), stop=_STOP
        )
        resp = await adapter.send(prompt)
        question = resp.text.strip()
        if not question or question.upper().startswith(_STOP):
            break
        answer = asker(question, i, max_questions)
        answers[question] = answer
    return answers
