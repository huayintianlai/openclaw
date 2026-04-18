# OpenClaw Backup and Restore

This repo now uses a restic-based backup flow with two backup profiles:

- `core` (daily): config + key runtime state
- `full` (weekly): `core` + session `.jsonl` bodies

Current plugin source backup targets are the actively mounted runtime plugins:

- `plugins/knowledge-search-plugin`
- `plugins/tavily-search-plugin`

## 1) Prerequisites

1. Install `restic` and `jq`
2. Create backup env file:

```bash
mkdir -p /Users/xiaojiujiu2/Documents/openclaw-docker/backups
cp /Users/xiaojiujiu2/Documents/openclaw-docker/scripts/backup.env.example \
  /Users/xiaojiujiu2/Documents/openclaw-docker/backups/backup.env
chmod 600 /Users/xiaojiujiu2/Documents/openclaw-docker/backups/backup.env
```

3. Fill `/Users/xiaojiujiu2/Documents/openclaw-docker/backups/backup.env` with real credentials.

## 2) Backup Commands

```bash
cd /Users/xiaojiujiu2/Documents/openclaw-docker

# Daily backup range
./scripts/backup_openclaw.sh backup --profile core --repo both

# Weekly backup range
./scripts/backup_openclaw.sh backup --profile full --repo both

# Manual integrity verify
./scripts/backup_openclaw.sh verify --repo both

# Pre-change forced snapshot (before editing .env/openclaw.json/docker-compose.yml, or before upgrade)
./scripts/backup_openclaw.sh prechange --tag before_upgrade_20260305 --repo both
```

Backup report is written to:

- `/Users/xiaojiujiu2/Documents/openclaw-docker/backups/reports/latest.json`
- mirrored copy for in-container agents:
  `/Users/xiaojiujiu2/Documents/openclaw-docker/instances/<instance>/data/state/backup/latest.json`

## 3) Scheduler

Use:

```bash
crontab /Users/xiaojiujiu2/Documents/openclaw-docker/scripts/backup_crontab.example
```

Current schedule (`Asia/Shanghai`):

- daily `03:15`: `core` backup
- weekly Sunday `03:40`: `full` backup
- weekly Sunday `04:20`: verify
- first Saturday `05:10`: non-production restore drill

## 4) Restore

```bash
cd /Users/xiaojiujiu2/Documents/openclaw-docker

# Validate snapshot + instance path first
./scripts/restore_openclaw.sh dry-run --snapshot <snapshot_id> --instance kent --repo both

# Restore into a temp dir (must be empty)
mkdir -p /tmp/openclaw-restore-kent
./scripts/restore_openclaw.sh restore \
  --snapshot <snapshot_id> \
  --instance kent \
  --target /tmp/openclaw-restore-kent \
  --repo both
```

After restore, compare restored files first, then apply to production paths.

## 5) Recovery Runbook

1. `docker compose -p openclaw down`
2. `restore_openclaw.sh dry-run`
3. restore to temp dir and verify key files
4. copy to live paths
5. `docker compose -p openclaw up -d`
6. `openclaw doctor --non-interactive`

## 6) Monthly Drill

- Every first Saturday: do a non-production restore to a temporary directory.
- Manual drill command:

```bash
./scripts/monthly_restore_drill.sh --instance kent --repo local
```

- Keep a short drill report with:
  - start/end time
  - snapshot used
  - failed steps
  - fixes required before next drill
