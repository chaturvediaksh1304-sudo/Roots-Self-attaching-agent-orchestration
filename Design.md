# Design.md — Roots

No UI. "Design" here means terminal output conventions, markdown formatting standards, and voice — the things that make a CLI tool feel considered instead of default-boilerplate. Matters extra because this is also a portfolio piece.

## Terminal output conventions
- **Color use (via `click`/`rich` if adopted, minimal otherwise)**: status colors only, never decorative.
  - Green — success / phase complete
  - Yellow — waiting on user input (grill questions)
  - Red — failure / self-repair triggered
  - Dim gray — background info (token counts, file paths)
  - No color for normal informational output — default terminal color.
- **No spinners/animations that hide what's happening.** Show real progress lines: `[2/4] Dispatching subagent: api-research...` not a generic loading bar. User should be able to scroll back and see exactly what ran, in order.
- **Grill phase formatting**: one question at a time, clearly numbered against the max (`Q2/4`), so the user knows how much is left. No walls of text before the question.
- **Subagent dispatch summary**: table-like aligned output, not prose, when listing active subagents — name, task boundary (one line), status.

## Markdown file conventions (Memory.md, result.md, history records)
- Every generated `.md` file starts with a frontmatter-style header block: goal, timestamp, status.
- Headings used structurally, not decoratively — no emoji headers, no ALL CAPS section titles.
- Subagent task boundaries always stated as a single explicit sentence, never a paragraph — keeps decomposition auditable at a glance.
- Result files separate "summary" (top, short) from "full detail" (below, collapsible in spirit — i.e. clearly separated by a horizontal rule) so orchestrator-facing summaries and human-facing detail don't get confused.

## Voice
- Direct, technical, no filler. Tool output reads like a competent engineer's terminal, not a chatbot.
- Error messages state what happened and what to do next — never "Oops! Something went wrong."
- No exclamation points in CLI output. No "Great! Let's get started!" — just start.

## Naming conventions
- Subagent files named by role, kebab-case: `api-research.md`, `schema-design.md` — never `agent-1.md`, `agent-2.md`.
- History run folders: `<ISO-timestamp>-<goal-slug>` — sortable and human-scannable in a file listing.

## Branding (portfolio surface — README, repo, any demo recording)
- Name: **Roots** — visual/textual motif if any branding is added later (README banner, etc.) should lean into the "attaches to and grows with any project" idea — understated, not cutesy. No mascot.
- Typography/colors for README banner (if made): stick to standard GitHub-README-safe formatting — no reliance on custom fonts, since this renders in plain markdown contexts (GitHub, PyPI).
