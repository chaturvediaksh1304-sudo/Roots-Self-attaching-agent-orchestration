# PRD.md — Roots

## What this is
Roots is a self-attaching agent orchestration system. Drop it into any project (via Claude Code plugin or standalone CLI) and it grills the user on their goal, decomposes the goal into parallel subtasks, dynamically generates specialized subagents to execute those subtasks, and improves itself over time — both by repairing its own subagent prompts when they fail, and by learning which subagent configurations work well so it can reuse and evolve them across future projects.

Roots is not a research assistant and not a coding agent itself. It is the meta-layer that builds and runs the right team of agents for whatever the attached project needs — coding, research, content, ops, anything.

## Problem
Building a multi-agent system by hand for every new project is slow and repetitive. Most people either (a) use one general-purpose agent for everything, wasting tokens on tasks that need real decomposition, or (b) hand-roll subagents per project with no memory of what worked last time. There's no tool that treats "spin up the right team of agents for this specific goal" as a repeatable, improvable process.

## Target users
1. **Solo dev (primary)** — attaches Roots to personal projects, wants fast task decomposition without hand-writing subagent configs every time.
2. **Open-source adopters** — other developers who install Roots into their own repos; needs to be model-agnostic and not assume Anthropic-only tooling.
3. **Portfolio/resume audience** — recruiters/hiring managers evaluating this as a demonstration of systems thinking around agent orchestration. Code quality, README clarity, and demo-ability matter as much as function.

## Core features (MVP → full)
- **Attach**: `roots init` in any project directory. Detects project type (language, framework) via lightweight scan, writes local config.
- **Grill**: interactive CLI flow that asks the user clarifying questions (max ~4, one at a time, adaptive) until the goal, scope, output format, and constraints are clear. Never blind-fires all questions upfront.
- **Decompose**: lead orchestrator breaks the goal into independent subtasks. Explicit non-overlapping boundaries per subtask (this is the #1 failure mode in multi-agent systems — duplicate work).
- **Generate**: writes subagent definition files (role, tool allowlist, output format) dynamically based on the decomposition — not from a fixed template library.
- **Dispatch**: runs subagents in parallel where genuinely independent; sequential where dependent.
- **Synthesize**: merges subagent outputs (short structured summaries, not raw traces) into a final result for the user.
- **Self-repair (Phase 2)**: when a subagent fails or produces low-quality output, orchestrator diagnoses the prompt/tool mismatch and rewrites the subagent definition, then retries.
- **Config evolution (Phase 3)**: Roots tracks which subagent configs succeeded across runs/projects and reuses or adapts them for similar future tasks, instead of generating from scratch every time.
- **Memory**: persistent local record of plan, progress, and subagent outcomes so a new chat/session doesn't lose context or force a full codebase re-read.

## Non-goals (v1)
- No UI/dashboard — terminal + markdown only.
- No hosted/cloud version — local-first, cloud sync is a later optional phase.
- Not tied to Claude models specifically — model-agnostic via config, though Claude Code is the primary integration target.
- Not a replacement for domain-specific agents (coding agents, research agents) — Roots orchestrates them, doesn't replace them.

## Success criteria
- Can attach to an arbitrary project and produce a correct subtask decomposition without the user hand-writing subagent files.
- Measurable reduction in duplicate/wasted subagent work run-over-run (self-repair working).
- Config reuse rate increases over time on similar task types (evolution working).
- A recruiter/engineer can read the repo and understand the architecture in under 10 minutes.
