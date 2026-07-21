"""Read/write local memory files + append-only run history.

History (`.roots/history/`) is append-only (Rules.md): archiving a run copies
its record in and never overwrites or deletes a prior run.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from .schema import MemoryState

MEMORY_REL = Path(".roots/memory.md")
HISTORY_REL = Path(".roots/history")


def write_memory(root: Path, state: MemoryState) -> Path:
    path = root / MEMORY_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(state.render())
    return path


def read_memory(root: Path) -> str:
    path = root / MEMORY_REL
    if not path.exists():
        raise FileNotFoundError(f"no {MEMORY_REL}. Run `roots run` first.")
    return path.read_text()


def archive_run(root: Path, slug: str, timestamp: str) -> Path:
    """Snapshot the current run's artifacts into append-only history.
    Folder name is `<timestamp>-<slug>` so a file listing sorts chronologically
    and stays human-scannable (Design.md). Copies the standard run artifacts
    (decomposition.json, agents/, result.md) per Architecture.md."""
    roots_dir = root / ".roots"
    dest = root / HISTORY_REL / f"{timestamp}-{slug}"
    if dest.exists():
        raise FileExistsError(
            f"history record {dest} already exists; history is append-only."
        )
    dest.mkdir(parents=True)
    for name in ("decomposition.json", "result.md"):
        src = roots_dir / name
        if src.exists():
            shutil.copy2(src, dest / name)
    if (roots_dir / "agents").exists():
        shutil.copytree(roots_dir / "agents", dest / "agents")
    return dest


class SyncBackend:
    """Optional cloud-sync interface — stubbed for v1 (Architecture.md).
    Not implemented; exists so the seam is defined, not so it works."""

    def push(self, root: Path) -> None:
        raise NotImplementedError("cloud sync is not implemented in v1")

    def pull(self, root: Path) -> None:
        raise NotImplementedError("cloud sync is not implemented in v1")
