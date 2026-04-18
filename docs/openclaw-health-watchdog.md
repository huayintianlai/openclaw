# OpenClaw 24h Health Watchdog

This watchdog wraps `scripts/healthcheck_openclaw.sh` and adds:

- baseline ignore list (known issues)
- new issue vs recovered issue detection
- 24h daily summary report

## Files

- script: `/Users/xiaojiujiu2/Documents/openclaw-docker/scripts/health_watchdog.sh`
- baseline: `/Users/xiaojiujiu2/Documents/openclaw-docker/scripts/health_watchdog_baseline.json`
- outputs:
  - `/Users/xiaojiujiu2/Documents/openclaw-docker/backups/reports/health/watchdog/latest.md`
  - `/Users/xiaojiujiu2/Documents/openclaw-docker/backups/reports/health/watchdog/latest.json`
  - `/Users/xiaojiujiu2/Documents/openclaw-docker/backups/reports/health/watchdog/daily-latest.md`
  - raw reports under `/Users/xiaojiujiu2/Documents/openclaw-docker/backups/reports/health/watchdog/raw/`

## Run once

```bash
cd /Users/xiaojiujiu2/Documents/openclaw-docker

# quick check
./scripts/health_watchdog.sh run --instance kent --level quick

# full check
./scripts/health_watchdog.sh run --instance kent --level full

# 24h summary
./scripts/health_watchdog.sh daily-summary --hours 24
```

## Exit codes for `run`

- `0`: no new issue (steady or clean)
- `1`: new fail detected
- `2`: new warn detected
- `3`: script/runtime error

## Baseline tuning

Edit `scripts/health_watchdog_baseline.json`:

```json
{
  "ignore": [
    {
      "instance": "kent",
      "layer": "L2",
      "name": "models.probe",
      "status": "warn",
      "code": "MODELS_PROBE_PARTIAL"
    }
  ]
}
```

Match rule is exact for fields you provide. Missing fields are treated as wildcard.
