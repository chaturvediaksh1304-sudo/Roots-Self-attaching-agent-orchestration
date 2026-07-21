# Architecture.md — Roots

## High-level flow
```
roots init  →  Grill (CLI Q&A)  →  Orchestrator plans  →  Generate subagent configs
     →  Dispatch (parallel/sequential)  →  Subagents execute  →  Synthesize
     →  Write results + update Memory  →  (on failure) Self-repair loop
     →  (over time) Config evolution across runs/projects
```

Roots has two runtime shells over one shared core:
- **Plugin mode**: lives in `.claude/` of the attached project, orchestrator agent is a Claude Code subagent itself, dispatch uses Claude Code's native `Task` tool.
- **CLI mode**: `roots` command runs standalone, calls whatever LLM backend is configured (Claude API, or any model via adapter), manages its own dispatch loop instead of relying on Claude Code's Task tool.

Both modes share the same core Python package — only the dispatch/execution adapter differs.

## Folder structure (the Roots package itself)
```
roots/
├── pyproject.toml
├── README.md
├── roots/
│   ├── __init__.py
│   ├── cli.py                  # entry point: roots init / run / status
│   ├── core/
│   │   ├── orchestrator.py     # grill + decompose + synthesize logic
│   │   ├── grill.py            # adaptive Q&A engine
│   │   ├── decomposer.py       # goal → subtask boundary logic
│   │   ├── subagent_gen.py     # writes subagent config files dynamically
│   │   ├── dispatcher.py       # parallel/sequential execution, adapter interface
│   │   ├── synthesizer.py      # merges subagent outputs
│   │   ├── self_repair.py      # Phase 2: diagnoses + rewrites failing subagent configs
│   │   └── evolution.py        # Phase 3: tracks + reuses successful configs across runs
│   ├── adapters/
│   │   ├── base.py             # model-agnostic interface (LLMAdapter ABC)
│   │   ├── claude_code.py      # uses Claude Code's Task tool when running as plugin
│   │   ├── anthropic_api.py    # direct Claude API calls (CLI mode)
│   │   └── generic_openai.py   # OpenAI-compatible endpoint adapter (model-agnostic)
│   ├── memory/
│   │   ├── store.py            # read/write local memory files
│   │   └── schema.py           # memory file structure/validation
│   └── config/
│       └── project_config.py   # per-project settings (.roots/config.yaml)
├── tests/
└── examples/
```

## Folder structure (inside an attached project, after `roots init`)
```
your-project/
├── .roots/
│   ├── config.yaml           # project-level Roots settings, model backend choice
│   ├── memory.md             # current run's persistent context (see Memory.md)
│   ├── agents/                # dynamically generated subagent configs, this run
│   │   └── <subagent-name>.md
│   └── history/                # past run configs, outcomes — feeds evolution.py
│       └── <timestamp>-<goal-slug>/
│           ├── decomposition.json
│           ├── agents/
│           └── result.md
└── .claude/                   # only if plugin mode — Claude Code native integration
    └── agents/
        └── roots-orchestrator.md
```

## Technical stack
- **Language**: Python 3.11+
- **CLI framework**: `click` (or `typer` — pick one, don't mix)
- **Config**: YAML for project config, Markdown for human-facing docs/memory, JSON for machine-facing history records
- **Model adapters**: thin ABC interface (`LLMAdapter`) — `send(prompt, tools) -> response`. Concrete adapters for Anthropic API, Claude Code Task tool, and a generic OpenAI-compatible adapter for model-agnostic support.
- **Parallelism**: `asyncio` for CLI-mode dispatch (subagents run as concurrent async calls); Claude Code's native `Task` tool handles concurrency in plugin mode.
- **Storage**: flat files only for v1 (YAML/JSON/MD) — no database. SQLite is a candidate for Phase 3 evolution-tracking if flat-file history search becomes too slow, not before.
- **No cloud dependency in v1.** Optional sync is a stubbed-out interface in `memory/store.py`, not implemented.

## Key architectural decisions
1. **Core is adapter-based, not Claude-specific.** `orchestrator.py` never calls a model API directly — it goes through `LLMAdapter`. This is what makes "model-agnostic" actually true rather than aspirational.
2. **Subagent configs are files, not in-memory objects.** Every generated subagent is a real `.md`/`.yaml` file on disk before dispatch. This makes self-repair (Phase 2) simple — repairing a subagent means editing its file and re-dispatching, and it makes the system inspectable/debuggable by a human at any point.
3. **History is the substrate for evolution.** `.roots/history/` is append-only. `evolution.py` reads past decompositions + outcomes to decide whether to reuse a config verbatim, adapt it, or generate fresh. Nothing is deleted; evolution is analysis over the log, not mutation of it.
4. **Synthesis never receives raw subagent reasoning.** Subagents write full output to their own result file; only a short structured summary + file reference goes back to the orchestrator. Keeps orchestrator context small regardless of how much work subagents did (per Anthropic's "game of telephone" lesson).
