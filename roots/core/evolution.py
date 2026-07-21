"""Phase 3 — config evolution across runs/projects. NOT IMPLEMENTED in Phase 1.

Intentionally a stub: Rules.md forbids building the evolution engine before the
base loop is working and tested. This module exists only so the package tree
matches Architecture.md. Phase 3 will index `.roots/history/`, reuse or adapt
successful subagent configs by task-type similarity, and track reuse success
rate. History is append-only — evolution is analysis over the log, never
mutation of it. See Phases.md.
"""

from __future__ import annotations


def suggest_reuse(*args, **kwargs):
    raise NotImplementedError("config evolution is Phase 3; not implemented yet")
