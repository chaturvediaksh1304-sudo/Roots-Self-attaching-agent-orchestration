# Memory.md — Template

This file is NOT filled in at project start. It gets created for real (at `.roots/memory.md` inside the Roots repo itself, since Roots is being built by an AI coding on itself) once implementation begins, and updated after every meaningful chunk of work. Purpose: any new chat/session picks this up instead of re-reading the whole codebase or re-deriving state from scratch.

Template structure to use once coding starts:

```markdown
# Memory — Roots (self-build)

## Current phase
Phase 1 — Core orchestration loop

## Status as of <timestamp>
- [x] roots init scaffold done
- [x] grill engine — basic version working
- [ ] decomposer — in progress, boundary-overlap detection not done yet
- [ ] subagent generator — not started
- [ ] dispatcher — not started
- [ ] synthesizer — not started

## Key decisions made this session
- Chose `click` over `typer` — <one-line reason>
- Adapter interface finalized: `send(prompt, tools) -> LLMResponse` — see adapters/base.py

## Known issues / open questions
- <anything unresolved that next session needs to know>

## Files touched this session
- roots/core/decomposer.py (new)
- roots/core/orchestrator.py (edited — added grill call)

## Next step
Finish boundary-overlap detection in decomposer.py, then write tests before touching subagent_gen.py.
```

## Rules for using this file once active
- Update at the end of every work session, not just at phase boundaries — cheap to write, expensive to lose.
- Keep it short. This is a pointer to state, not a full changelog — link to specific files/commits rather than pasting code into it.
- Never let it go stale mid-session and get read by a fresh context as if current — if a session ends mid-task, note that explicitly ("left mid-implementation, decomposer.py has syntax error, do not trust current state").
- One file, not one-per-phase — old phases collapse to a single completed-checkbox line once done, detail moves to git history.
