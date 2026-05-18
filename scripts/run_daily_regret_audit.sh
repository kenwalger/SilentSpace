#!/usr/bin/env bash
# SilentSpace Guardian — Daily Meeting Regret Audit
#
# Intended schedule: weekdays at 17:00 (5 PM local time)
# Output:           reports/daily_digest.md
#
# Usage:
#   bash scripts/run_daily_regret_audit.sh
#
# Manual verification:
#   bash scripts/run_daily_regret_audit.sh && cat reports/daily_digest.md
#
# Cron entry (Linux/macOS/WSL):
#   0 17 * * 1-5  cd /path/to/silentspace-guardian && bash scripts/run_daily_regret_audit.sh >> logs/daily.log 2>&1
#
# Windows Task Scheduler: see docs/scheduled_audits.md

set -euo pipefail
cd "$(dirname "$0")/.."

PY=""
for cmd in python python3; do
    if command -v "$cmd" >/dev/null 2>&1; then
        PY="$cmd"
        break
    fi
done

if [[ -z "$PY" ]]; then
    echo "ERROR: Python not found. Install Python 3.9+ and add it to PATH." >&2
    exit 1
fi

echo "SilentSpace Guardian — Daily Regret Audit"
echo "Date: $(date +%Y-%m-%d)"
echo "------------------------------------------"

"$PY" python/generate_daily_digest.py

echo "------------------------------------------"
echo "Done. Report: reports/daily_digest.md"
