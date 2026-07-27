<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/White-logo.png">
    <img src="assets/Blac-logo.png" alt="Roots" width="620">
  </picture>
</p>

<p align="center">
  <strong>Self-attaching agent orchestration!</strong><br>
  Drop it into any project. It grills you on the goal, decomposes it into
  non-overlapping subtasks, generates specialized subagents to run them, and
  synthesizes the result.
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-blue">
  <img alt="Claude Code plugin" src="https://img.shields.io/badge/Claude%20Code-plugin-8A63D2">
  <img alt="Status" src="https://img.shields.io/badge/status-phase%201-orange">
</p>

---

Roots is **not** a coding agent or a research agent. It is the meta-layer that
builds and runs the right *team* of agents for whatever the attached project
needs. You point it at a folder; it figures out the rest.

It is **model-agnostic**: the core never imports a model SDK. Every model call
routes through a single adapter interface, so the same orchestration runs as a
keyless Claude Code plugin, against Anthropic, or against any OpenAI-compatible
endpoint.

## How it works

```
attach ──▶ grill ──▶ decompose ──▶ generate ──▶ dispatch ──▶ synthesize ──▶ memory
```

| Step | What happens |
|------|--------------|
| **attach**    | Scan the project, detect the stack, write `.roots/config.yaml`. |
| **grill**     | Interrogate you until the goal is unambiguous. |
| **decompose** | Split the goal into non-overlapping subtasks (the core invariant: boundaries must not overlap). |
| **generate**  | Write a specialized subagent config per subtask — role, boundary, tool allowlist. |
| **dispatch**  | Run the subagents in dependency order; independent ones run in parallel. |
| **synthesize**| Merge subagent outputs into one coherent result. |
| **memory**    | Append-only snapshot of the whole run under `.roots/history/`. |

Everything a run touches lands on disk under `.roots/`, so every step is
inspectable and re-runnable.

## Two ways to run it

| | **Claude Code plugin** | **Standalone CLI** |
|---|---|---|
| Command | `/roots <goal>` | `roots run --goal "<goal>"` |
| Runtime | Claude Code (Task tool) | Python process |
| **API key** | **None** — uses your Claude session | Required (`ANTHROPIC_API_KEY` or OpenAI-compatible) |
| Best for | Interactive work inside Claude Code | Headless / CI / automation |
| Subagents | Native Claude Code Task subagents | Direct model calls via an adapter |

Both write the **same** `.roots/` artifacts, so a run is portable between them.

---

# Install

## 1. As a Claude Code plugin — recommended, keyless

**Requirements:** [Claude Code](https://docs.anthropic.com/en/docs/claude-code).
No Python, no API key.

Add the marketplace, then install the plugin. From your terminal:

```bash
claude plugin marketplace add chaturvediaksh1304-sudo/Roots-Self-attaching-agent-orchestration
claude plugin install roots@roots
```

Or from inside a Claude Code session (interactive):

```
/plugin marketplace add chaturvediaksh1304-sudo/Roots-Self-attaching-agent-orchestration
/plugin install roots@roots
```

The `/roots` command becomes available in your **next** session. Verify:

```bash
claude plugin list          # roots@roots → enabled
claude plugin details roots@roots
```

Then, from any project:

```
/roots Add a contact form with email validation
```

In plugin mode Claude Code *is* the runtime: `/roots` runs the full loop and
dispatches each subagent through Claude Code's native **Task tool**, so it uses
your existing Claude session — no `ANTHROPIC_API_KEY`, no OpenAI endpoint.

## 2. As a CLI — pip / pipx / uv / source

**Requirements:**
- **Python 3.11+**
- A model backend + key: `ANTHROPIC_API_KEY` (default), **or** `OPENAI_BASE_URL`
  + `OPENAI_API_KEY` for any OpenAI-compatible endpoint.

Pick whichever tool you already use — all install the `roots` CLI onto your PATH.

**pipx** (recommended — isolated global CLI):

```bash
pipx install git+https://github.com/chaturvediaksh1304-sudo/Roots-Self-attaching-agent-orchestration.git
```

**pip:**

```bash
pip install git+https://github.com/chaturvediaksh1304-sudo/Roots-Self-attaching-agent-orchestration.git
```

**uv:**

```bash
uv tool install git+https://github.com/chaturvediaksh1304-sudo/Roots-Self-attaching-agent-orchestration.git
```

**From source** (for development):

```bash
git clone https://github.com/chaturvediaksh1304-sudo/Roots-Self-attaching-agent-orchestration.git
cd Roots-Self-attaching-agent-orchestration
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Verify:

```bash
roots --help
```

---

# Usage

## Plugin

```
/roots <what you want to build>
```

`/roots` grills you (via interactive questions) if the goal is fuzzy, then runs
the whole loop and reports the result. No key, no setup beyond install.

## CLI

```bash
cd your-project

roots init                 # scan project, write .roots/config.yaml
export ANTHROPIC_API_KEY=sk-...
roots run --goal "Add a contact form with email validation"
roots status               # print the current run's memory
```

Omit `--goal` and Roots prompts (and grills) you for it. The three commands are
the whole surface: `init`, `run`, `status`.

### Configuring the backend (CLI)

`roots init` writes `.roots/config.yaml`. Default backend is `anthropic`. For any
OpenAI-compatible endpoint:

```yaml
# .roots/config.yaml
backend: generic_openai
```

```bash
export OPENAI_BASE_URL=https://your-endpoint/v1
export OPENAI_API_KEY=...
```

Available adapters: `anthropic`, `generic_openai`, `claude_code`.

---

## What a run produces

Every run writes to `.roots/` in the current project:

```
.roots/
├── config.yaml                     # backend + detected stack
├── decomposition.json              # { goal, subtasks: [ {name, boundary, depends_on, tools} ] }
├── agents/
│   ├── <role>.md                   # subagent config: role, boundary, tool allowlist, output contract
│   └── <role>.result.md            # subagent output: SUMMARY line + full detail
├── result.md                       # the synthesized final result
├── memory.md                       # goal, status, plan, per-subagent outcomes, next step
└── history/<timestamp>-<slug>/     # append-only snapshot of this run (never overwritten)
```

- **Subagents are real files, not in-memory objects** — so a run is inspectable,
  and a future self-repair phase becomes a plain file edit.
- **Dispatch respects dependencies.** Subtasks are grouped into topological
  layers: layer 0 has no dependencies; each later layer depends only on earlier
  ones. Within a layer, subagents run in parallel; across layers, in order.
- **History is append-only.** Each run is snapshotted under `history/` and never
  overwritten, so you keep a full audit trail.

See [`examples/`](examples/) for an end-to-end throwaway-project walkthrough.

## Project layout

Core orchestration lives in `roots/core/`; it never imports a model SDK
directly — every model call goes through `roots/adapters/base.py::LLMAdapter`,
which is what makes Roots model-agnostic.

```
roots/
├── cli.py            # init / run / status
├── core/             # orchestrator, grill, decomposer, dispatcher, synthesizer
├── adapters/         # anthropic_api, generic_openai, claude_code (+ base)
├── memory/           # append-only run store + schema
└── config/           # project detection + .roots/config.yaml
```

Design docs: [`Architecture.md`](Architecture.md) · [`Design.md`](Design.md) ·
[`PRD.md`](PRD.md) · [`Phases.md`](Phases.md) · [`Rules.md`](Rules.md)

## Status & roadmap

**Phase 1** — core orchestration loop
(`attach → grill → decompose → generate → dispatch → synthesize → memory`) is
implemented and shipped, for both the plugin and the CLI.

- **Phase 2** — self-repair (stubbed, not implemented)
- **Phase 3** — config evolution (stubbed, not implemented)

See [`Phases.md`](Phases.md).

## Tests

```bash
pytest
```

## Uninstall

Plugin:

```bash
claude plugin uninstall roots@roots
claude plugin marketplace remove roots
```

CLI:

```bash
pipx uninstall roots        # or: pip uninstall roots / uv tool uninstall roots
```
