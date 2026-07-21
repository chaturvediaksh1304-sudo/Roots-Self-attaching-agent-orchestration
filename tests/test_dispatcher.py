import asyncio

import pytest

from roots.adapters.base import AdapterError, LLMAdapter, LLMResponse
from roots.core.decomposer import Decomposition, Subtask
from roots.core.dispatcher import (
    DependencyError,
    dispatch,
    plan_layers,
)
from roots.core.subagent_gen import generate


# --- pure: layering ----------------------------------------------------------

def test_plan_layers_independent_are_one_layer():
    subs = [Subtask("a", "do a"), Subtask("b", "do b")]
    assert plan_layers(subs) == [["a", "b"]]


def test_plan_layers_chain_is_sequential():
    subs = [
        Subtask("a", "do a"),
        Subtask("b", "do b", depends_on=["a"]),
        Subtask("c", "do c", depends_on=["b"]),
    ]
    assert plan_layers(subs) == [["a"], ["b"], ["c"]]


def test_plan_layers_diamond():
    subs = [
        Subtask("a", "do a"),
        Subtask("b", "do b", depends_on=["a"]),
        Subtask("c", "do c", depends_on=["a"]),
        Subtask("d", "do d", depends_on=["b", "c"]),
    ]
    assert plan_layers(subs) == [["a"], ["b", "c"], ["d"]]


def test_plan_layers_rejects_cycle():
    subs = [
        Subtask("a", "do a", depends_on=["b"]),
        Subtask("b", "do b", depends_on=["a"]),
    ]
    with pytest.raises(DependencyError):
        plan_layers(subs)


# --- async: real parallelism vs sequencing -----------------------------------

class _OrderAdapter(LLMAdapter):
    """Records enter/exit order to prove concurrency within a layer."""

    def __init__(self, delay=0.05):
        self.delay = delay
        self.events = []

    async def send(self, prompt, tools=None):
        name = prompt.split("role: ", 1)[1].split("\n", 1)[0]
        self.events.append(("enter", name))
        await asyncio.sleep(self.delay)
        self.events.append(("exit", name))
        return LLMResponse(text=f"SUMMARY: done {name}\n\nbody")


def _dispatch(decomp, adapter, tmp_path):
    paths = generate(tmp_path, decomp.subtasks)
    return asyncio.run(dispatch(decomp, adapter, paths, timeout=5))


def test_independent_subtasks_run_concurrently(tmp_path):
    decomp = Decomposition("g", [Subtask("a", "do a"), Subtask("b", "do b")])
    adapter = _OrderAdapter()
    _dispatch(decomp, adapter, tmp_path)
    # both enter before either exits -> genuinely parallel, not serialized
    assert adapter.events[0][0] == "enter"
    assert adapter.events[1][0] == "enter"


def test_dependent_subtask_waits_for_dependency(tmp_path):
    decomp = Decomposition("g", [
        Subtask("a", "do a"),
        Subtask("b", "do b", depends_on=["a"]),
    ])
    adapter = _OrderAdapter()
    _dispatch(decomp, adapter, tmp_path)
    # a must fully exit before b enters
    assert adapter.events == [
        ("enter", "a"), ("exit", "a"), ("enter", "b"), ("exit", "b"),
    ]


# --- async: failure handling -------------------------------------------------

class _RaisingAdapter(LLMAdapter):
    async def send(self, prompt, tools=None):
        raise AdapterError("boom")


class _EmptyAdapter(LLMAdapter):
    async def send(self, prompt, tools=None):
        return LLMResponse(text="")


class _SlowAdapter(LLMAdapter):
    async def send(self, prompt, tools=None):
        await asyncio.sleep(1.0)
        return LLMResponse(text="SUMMARY: late")


def test_adapter_failure_is_recorded_not_raised(tmp_path):
    decomp = Decomposition("g", [Subtask("a", "do a")])
    results = _dispatch(decomp, _RaisingAdapter(), tmp_path)
    assert results[0].status == "failed" and "boom" in results[0].summary
    assert "Failed" in (tmp_path / ".roots/agents/a.result.md").read_text()


def test_empty_output_is_failure(tmp_path):
    decomp = Decomposition("g", [Subtask("a", "do a")])
    results = _dispatch(decomp, _EmptyAdapter(), tmp_path)
    assert results[0].status == "failed" and "malformed" in results[0].summary


def test_timeout_is_failure(tmp_path):
    decomp = Decomposition("g", [Subtask("a", "do a")])
    paths = generate(tmp_path, decomp.subtasks)
    results = asyncio.run(dispatch(decomp, _SlowAdapter(), paths, timeout=0.05))
    assert results[0].status == "failed" and "timed out" in results[0].summary


def test_success_writes_summary_and_detail(tmp_path):
    decomp = Decomposition("g", [Subtask("a", "do a")])
    results = _dispatch(decomp, _OrderAdapter(), tmp_path)
    assert results[0].status == "ok"
    content = (tmp_path / ".roots/agents/a.result.md").read_text()
    assert "## Summary" in content and "## Full detail" in content
