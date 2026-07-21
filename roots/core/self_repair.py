"""Phase 2 — self-repair loop. NOT IMPLEMENTED in Phase 1.

Intentionally a stub: Rules.md forbids building the self-repair loop before the
base orchestrate/dispatch/generate loop is working and tested. This module
exists only so the package tree matches Architecture.md. Phase 2 will diagnose
a failed subagent's config + output, rewrite the config file, log the change,
and redispatch with a capped retry count. See Phases.md.
"""

from __future__ import annotations


def repair(*args, **kwargs):
    raise NotImplementedError("self-repair is Phase 2; not implemented yet")
