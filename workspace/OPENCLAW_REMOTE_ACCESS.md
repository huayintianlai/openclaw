# OpenClaw Remote Access

Use the existing `frp + ssh` path to reach the Mac mini, then expose OpenClaw locally on your own machine.

## Fast path

Run this on your local machine:

```bash
bash openclaw_ui_via_frp.sh
```

Then open:

```text
http://127.0.0.1:18789/ui/
```

## One-liner

```bash
ssh -p 37847 xiaojiujiu2@frp5.ccszxc.site -N -L 18789:127.0.0.1:18789
```

## Why this works

- OpenClaw `2026.3.12` accepts Control UI over `localhost`.
- Direct LAN HTTP access is blocked by the current secure-context/device-identity checks.
- Reusing the existing `frp` SSH tunnel avoids exposing the gateway publicly.

## Optional flags

```bash
bash openclaw_ui_via_frp.sh --background --open
```

Environment overrides:

```bash
FRP_HOST=frp5.ccszxc.site \
FRP_PORT=37847 \
REMOTE_USER=xiaojiujiu2 \
LOCAL_PORT=18789 \
bash openclaw_ui_via_frp.sh
```
