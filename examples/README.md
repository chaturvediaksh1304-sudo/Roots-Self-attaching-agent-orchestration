# Examples

Try Roots against a throwaway project:

```
mkdir /tmp/demo && cd /tmp/demo
echo '{"dependencies": {"next": "1"}}' > package.json

roots init      # detects node/next, writes .roots/config.yaml
export ANTHROPIC_API_KEY=sk-...
roots run --goal "Add a contact form with email validation"
roots status
```

Inspect what ran:

- `.roots/agents/*.md` — the generated subagent configs (role, boundary, tools)
- `.roots/agents/*.result.md` — each subagent's output (summary + full detail)
- `.roots/result.md` — the synthesized final result
- `.roots/history/<timestamp>-<slug>/` — append-only snapshot of the run
