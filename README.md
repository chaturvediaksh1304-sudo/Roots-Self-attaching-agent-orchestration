<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/White-logo.png">
    <img src="assets/Blac-logo.png" alt="Roots" width="620">
  </picture>
</p>

<p align="center">
  <strong>Self-attaching agent orchestration.</strong><br>
  Drop it into any project. It grills you on the goal, decomposes it into
  non-overlapping subtasks, generates specialized subagents to run them, and
  synthesizes the result.
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-blue">
  <img alt="Status" src="https://img.shields.io/badge/status-phase%201-orange">
</p>

---

Roots is **not** a coding agent or a research agent. It is the meta-layer that
builds and runs the right *team* of agents for whatever the attached project
needs. You point it at a folder; it figures out the rest.

It is **model-agnostic**: the core never imports a model SDK. Every model call
routes through a single adapter interface, so the same orchestration runs on
Anthropic, any OpenAI-compatible endpoint, or the Claude Code CLI.

## How it works

```
attach ──▶ grill ──▶ decompose ──▶ generate ──▶ dispatch ──▶ synthesize ──▶ memory
```

| Step | What happens |
|------|--------------|
| **attach**    | Scan the project, detect stack, write `.roots/config.yaml`. |
| **grill**     | Interrogate you until the goal is unambiguous. |
| **decompose** | Split the goal into non-overlapping subtasks. |
| **generate**  | Write a specialized subagent per subtask (role, boundary, tools). |
| **dispatch**  | Run the subagents against their slices. |
| **synthesize**| Merge subagent outputs into one coherent result. |
| **memory**    | Append-only snapshot of the whole run under `.roots/history/`. |

## Requirements

- **Python 3.11+**
- A model backend + key:
  - `ANTHROPIC_API_KEY` (default backend), **or**
  - `OPENAI_BASE_URL` + `OPENAI_API_KEY` for any OpenAI-compatible endpoint.

## Install

Pick whichever tool you already use — all install the `roots` CLI onto your PATH.

### pipx (recommended — isolated global CLI)

```bash
pipx install git+https://github.com/chaturvediaksh1304-sudo/Roots-Self-attaching-agent-orchestration.git
```

### pip

```bash
pip install git+https://github.com/chaturvediaksh1304-sudo/Roots-Self-attaching-agent-orchestration.git
```

### uv

```bash
uv tool install git+https://github.com/chaturvediaksh1304-sudo/Roots-Self-attaching-agent-orchestration.git
```

### From source (for development)

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

## Use as a Claude Code plugin

Roots ships a thin [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
plugin that adds a `/roots` slash command. Add the marketplace, then install:

```
/plugin marketplace add chaturvediaksh1304-sudo/Roots-Self-attaching-agent-orchestration
/plugin install roots@roots
```

Then, from any project:

```
/roots Add a contact form with email validation
```

**No API key needed.** In plugin mode Claude Code *is* the runtime: `/roots`
runs the full loop (grill → decompose → generate → dispatch → synthesize) and
dispatches each subagent through Claude Code's native **Task tool**, so it uses
your existing Claude session — no `ANTHROPIC_API_KEY`, no OpenAI endpoint. It
writes the same `./.roots/` artifacts (`result.md`, `agents/`, `memory.md`,
append-only `history/`) as the CLI, so runs stay inspectable and compatible.

> The standalone **CLI** path (`roots run`) is different — it calls a model
> backend directly and **does** need `ANTHROPIC_API_KEY` or an OpenAI-compatible
> endpoint. Use the plugin for keyless runs, the CLI for headless/automation.

## Usage

```bash
cd your-project

roots init                 # scan project, write .roots/config.yaml
export ANTHROPIC_API_KEY=sk-...
roots run --goal "Add a contact form with email validation"
roots status               # print the current run's memory
```

Omit `--goal` and Roots prompts (and grills) you for it.

### Switching backends

`roots init` writes `.roots/config.yaml`. Default backend is `anthropic`. For
any OpenAI-compatible endpoint:

```yaml
# .roots/config.yaml
backend: generic_openai
```

```bash
export OPENAI_BASE_URL=https://your-endpoint/v1
export OPENAI_API_KEY=...
```

Available adapters: `anthropic`, `generic_openai`, `claude_code`.

### Inspecting a run

After `roots run`, everything is on disk under `.roots/`:

- `.roots/agents/*.md` — generated subagent configs (role, boundary, tools)
- `.roots/agents/*.result.md` — each subagent's output (summary + full detail)
- `.roots/result.md` — the synthesized final result
- `.roots/history/<timestamp>-<slug>/` — append-only snapshot of the run

See [`examples/`](examples/) for an end-to-end throwaway-project walkthrough.

## Layout

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

## Status

**Phase 1** — core orchestration loop
(`attach → grill → decompose → generate → dispatch → synthesize → memory`) is
implemented. Self-repair (Phase 2) and config evolution (Phase 3) are stubbed,
not implemented. See [`Phases.md`](Phases.md).

## Tests

```bash
pytest
```
