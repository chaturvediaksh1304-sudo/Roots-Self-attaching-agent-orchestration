---
description: Run Roots agent orchestration on the current project — grill, decompose, dispatch subagents, synthesize.
argument-hint: [goal]
---

You are driving the **Roots** CLI (`roots`), a self-attaching agent
orchestrator. Run it against the user's current working directory.

Goal (may be empty): `$ARGUMENTS`

Do this in order, stopping to report at each step:

1. **Ensure the CLI is installed.** Run `command -v roots`. If it is missing,
   install it once with:
   ```bash
   pipx install git+https://github.com/chaturvediaksh1304-sudo/Roots-Self-attaching-agent-orchestration.git
   ```
   (Fall back to `pip install ...` if `pipx` is unavailable.) Requires Python 3.11+.

2. **Check the backend key.** Roots defaults to the `anthropic` backend and reads
   `ANTHROPIC_API_KEY`. If it is unset, tell the user and stop — do not proceed
   without a key. (For an OpenAI-compatible endpoint, they set `backend:
   generic_openai` in `.roots/config.yaml` plus `OPENAI_BASE_URL` / `OPENAI_API_KEY`.)

3. **Attach if needed.** If `.roots/config.yaml` does not exist, run `roots init`
   to scan the project and write it. Show the detected stack.

4. **Run.** If a goal was given, run `roots run --goal "$ARGUMENTS"`. If not, run
   `roots run` and let it grill the user interactively.

5. **Report.** Run `roots status`, then point the user at the outputs:
   `.roots/result.md` (synthesized result) and `.roots/agents/` (per-subagent
   configs + results).

Never invent Roots subcommands — the only ones are `init`, `run`, `status`.
If any command errors, surface the exact error and stop.
