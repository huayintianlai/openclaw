#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -d "/Users/xiaojiujiu2/.openclaw/workspace/xiaodong" ]; then
  ROOT="/Users/xiaojiujiu2/.openclaw/workspace/xiaodong"
else
  ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi

SKILLS_DIR="$ROOT/skills"
BACKUPS_DIR="$ROOT/backups/skills"
STAMP="$(date +%Y%m%d_%H%M%S)"
TMP_FILE="$SKILLS_DIR/.self-upgrade-write-test.$STAMP"

if [ ! -d "$SKILLS_DIR" ]; then
  echo "FAIL: skills directory not found: $SKILLS_DIR" >&2
  exit 1
fi

mkdir -p "$BACKUPS_DIR"

echo "smoke-write-test" >"$TMP_FILE"
rm -f "$TMP_FILE"

status=0
skill_count=0

for skill_dir in "$SKILLS_DIR"/*; do
  [ -d "$skill_dir" ] || continue
  skill_count=$((skill_count + 1))
  skill_md="$skill_dir/SKILL.md"

  if [ ! -f "$skill_md" ]; then
    echo "FAIL: missing SKILL.md: $skill_md" >&2
    status=1
    continue
  fi

  if ! grep -q "^name:" "$skill_md"; then
    echo "WARN: missing 'name:' frontmatter in $skill_md" >&2
  fi
done

if [ "$skill_count" -eq 0 ]; then
  echo "WARN: no skill directories found under $SKILLS_DIR" >&2
fi

if [ "$status" -ne 0 ]; then
  echo "FAIL: smoke checks failed" >&2
  exit "$status"
fi

echo "OK: xiaodong self-upgrade smoke checks passed."
echo "ROOT=$ROOT"
echo "SKILLS=$SKILLS_DIR"
