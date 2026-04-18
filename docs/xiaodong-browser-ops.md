# Xiaodong Browser Route (Node Mode)

This project uses OpenClaw Route #3:

- Gateway runs in Docker (`kentclaw`).
- Browser runs on host node (`mac-browser-node`), controlled through gateway.
- Xiaodong browser tasks that should reuse the user's existing Chrome must use `browser(target="node", node="mac-browser-node", profile="chrome")`.
- Before agent control, the user must click the OpenClaw Browser Relay extension on the target Chrome tab and make sure the badge shows `ON`.

## Daily health checks

Run:

```bash
docker compose exec -T kentclaw openclaw nodes status
docker compose exec -T kentclaw openclaw browser profiles
docker compose exec -T kentclaw openclaw browser --browser-profile chrome tabs
```

Expected:

- node status includes `mac-browser-node` and `paired · connected`
- profile list includes `chrome`
- `openclaw browser --browser-profile chrome tabs` can see the attached target tab
- the target Chrome tab is attached with the OpenClaw Browser Relay extension and shows `ON`

## Adding a new browser task (maintainable pattern)

1. Create a dedicated skill under `instances/kentclaw/data/workspace/xiaodong/skills/<skill-name>/SKILL.md`.
2. In skill description, include:
   - exact trigger words
   - fixed URL/domain rules
   - fixed tool target/profile
   - explicit failure behavior
3. Add one hard-rule line in:
   - `instances/kentclaw/data/agents/xiaodong/agent/AGENTS.md`
   - `instances/kentclaw/data/workspace/xiaodong/AGENTS.md`
4. Add one smoke test script in `scripts/` for deterministic regression.

## Fast troubleshooting

1. Node disconnected:
   - check host service `openclaw node host status`
   - verify host and gateway token match (`OPENCLAW_GATEWAY_TOKEN`)
2. Browser opens wrong target or no tab is visible:
   - verify the target Chrome tab is attached and the extension badge shows `ON`
   - tighten skill frontmatter `description`
   - tighten agent/workspace AGENTS hard rules
3. Session keeps old bad behavior:
   - backup then rotate `agent:xiaodong:main` session entry in `instances/kentclaw/data/agents/xiaodong/sessions/sessions.json`
