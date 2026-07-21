"""End-to-end Phase 1 loop with a deterministic fake adapter (no network).

This is the offline integration proof for Phase 1's exit criteria: attach a
project, take a goal, produce a decomposed multi-agent result with no
hand-written configs and no duplicate work."""

import asyncio
import json

from roots.core import orchestrator
from tests.fake_adapter import FakeAdapter


def _handler(prompt: str) -> str:
    if "clarifying a project goal" in prompt:
        return "DONE"  # skip grill
    if "Decompose this goal" in prompt:
        return (
            '[{"name":"api-research","boundary":"Document the REST endpoints",'
            '"tools":["web"]},'
            '{"name":"schema-design","boundary":"Design the database tables",'
            '"depends_on":["api-research"],"tools":["fs"]}]'
        )
    role = prompt.split("role: ", 1)[1].split("\n", 1)[0]
    return f"SUMMARY: completed {role}\n\nfull body for {role}"


def test_full_loop(tmp_path):
    adapter = FakeAdapter(handler=_handler)
    result = asyncio.run(
        orchestrator.run("build an API client", tmp_path, adapter, asker=None)
    )

    # result + memory + history all written
    assert result.result_path.exists()
    assert result.memory_path.exists()
    assert result.history_path.exists()

    # two subagents, both ok, dependency respected (research before schema)
    assert [o.name for o in result.outcomes] == ["api-research", "schema-design"]
    assert all(o.status == "ok" for o in result.outcomes)

    # configs were generated to disk, named by role (no agent-1.md)
    assert (tmp_path / ".roots/agents/api-research.md").exists()
    assert (tmp_path / ".roots/agents/schema-design.md").exists()

    # decomposition persisted; history is a real snapshot
    decomp = json.loads((tmp_path / ".roots/decomposition.json").read_text())
    assert len(decomp["subtasks"]) == 2
    assert (result.history_path / "result.md").exists()
    assert (result.history_path / "agents").is_dir()

    # final result separates summary from full detail
    content = result.result_path.read_text()
    assert "## Summary" in content and "## Full detail" in content
