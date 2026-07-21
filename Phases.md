# Phases.md — Roots

Full self-improving architecture is the goal, but Phase 1 stays conservative and verifiable. Each phase must be working and tested before the next starts.

## Phase 1 — Core orchestration loop (no self-improvement yet)
Goal: prove the basic attach → grill → decompose → generate → dispatch → synthesize loop works end to end, on real tasks, before anything "improves" itself.

- [ ] `roots init` — scans project, writes `.roots/config.yaml`
- [ ] Grill engine — adaptive Q&A, max 4 questions, one at a time
- [ ] Decomposer — goal → subtasks with explicit non-overlapping boundaries
- [ ] Subagent generator — writes real config files to `.roots/agents/`
- [ ] Dispatcher — parallel execution for independent subtasks, sequential for dependent ones (Anthropic API adapter + Claude Code Task adapter both working)
- [ ] Synthesizer — merges subagent result files into final output
- [ ] Basic Memory.md write — records goal, plan, subagent outcomes for the run
- [ ] Manual test: run against 3 real tasks of increasing complexity (1-agent, 2-3 agent, 5+ agent), confirm no duplicate work and correct synthesis

**Exit criteria**: can attach to an arbitrary project, take a real goal, and produce a correct decomposed multi-agent result without hand-written subagent configs.

## Phase 2 — Self-repair loop
Goal: when a subagent fails or underperforms, orchestrator diagnoses and fixes it, on evidence — not speculative tuning.

- [ ] Failure detection — define what "failed" means (timeout, malformed output, tool error, low-quality flag)
- [ ] Diagnosis step — orchestrator reads failed subagent's config + output, identifies likely cause (bad tool allowlist, vague task boundary, wrong output format)
- [ ] Repair step — rewrites the subagent config file, logs the change and reason
- [ ] Retry — redispatches repaired subagent, caps retry count (don't loop forever)
- [ ] Test: intentionally misconfigure a subagent (bad tool access, vague instructions), confirm self-repair fixes it within N retries

**Exit criteria**: measurable reduction in failure rate on repeated similar tasks within a single project.

## Phase 3 — Config evolution across runs/projects
Goal: Roots remembers what worked and reuses/adapts it instead of generating from scratch every time.

- [ ] History indexing — read `.roots/history/` across runs, extract successful subagent configs by task-type similarity
- [ ] Reuse logic — decomposer/generator checks history before generating fresh; reuses verbatim, adapts, or falls back to fresh generation
- [ ] Evolution tracking — record which configs get reused/adapted and their success rate over time
- [ ] Cross-project support — history lookup works across multiple attached projects, not just current one (local machine scope for v1)
- [ ] Test: run same task-type twice in different projects, confirm second run reuses/adapts rather than regenerating from scratch, and measure token savings

**Exit criteria**: config reuse rate increases measurably over repeated similar tasks; token cost per equivalent task decreases run-over-run.

## Phase 4 — Polish & distribution (portfolio-facing)
- [ ] Plugin packaging for Claude Code marketplace-style install
- [ ] Standalone CLI packaging (`pip install roots` or similar)
- [ ] README with clear architecture diagram, demo GIF/recording, example run
- [ ] Optional cloud sync interface stub → real implementation (only if time allows, explicitly last)

**Exit criteria**: a stranger can install it, run it against a toy project, and understand what happened from the README alone.
