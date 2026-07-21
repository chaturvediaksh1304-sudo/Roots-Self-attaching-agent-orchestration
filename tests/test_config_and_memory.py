import pytest

from roots.config.project_config import init_project, load_config, scan_project
from roots.memory import store
from roots.memory.schema import MemoryState, SubagentOutcome


def test_scan_detects_python(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
    assert scan_project(tmp_path).language == "python"


def test_scan_detects_node_framework(tmp_path):
    (tmp_path / "package.json").write_text('{"dependencies": {"next": "1"}}')
    cfg = scan_project(tmp_path)
    assert cfg.language == "node" and cfg.framework == "next"


def test_init_is_idempotent_and_preserves_backend(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
    init_project(tmp_path)
    # user edits backend, then re-inits
    cfgfile = tmp_path / ".roots/config.yaml"
    cfgfile.write_text(cfgfile.read_text().replace("anthropic", "generic_openai"))
    again = init_project(tmp_path)
    assert again.backend == "generic_openai"  # preserved, not clobbered


def test_history_is_append_only(tmp_path):
    (tmp_path / ".roots").mkdir()
    (tmp_path / ".roots/result.md").write_text("r")
    store.archive_run(tmp_path, "slug", "2026-07-21T00:00:00+00:00")
    with pytest.raises(FileExistsError):
        store.archive_run(tmp_path, "slug", "2026-07-21T00:00:00+00:00")


def test_memory_render_has_frontmatter():
    state = MemoryState(
        goal="g", timestamp="t",
        outcomes=[SubagentOutcome(name="a", status="ok", summary="s",
                                  result_path="p")],
    )
    out = state.render()
    assert out.startswith("---") and "goal: g" in out and "- [x] a:" in out
