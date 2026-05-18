#!/usr/bin/env bash
# SilentSpace Guardian — Weekly Entropy Summary
#
# Intended schedule: Fridays at 16:00 (4 PM local time)
# Output:           reports/weekly_entropy.md
#
# Usage:
#   bash scripts/run_weekly_entropy_summary.sh
#
# Manual verification:
#   bash scripts/run_weekly_entropy_summary.sh && cat reports/weekly_entropy.md
#
# Cron entry (Linux/macOS/WSL):
#   0 16 * * 5  cd /path/to/silentspace-guardian && bash scripts/run_weekly_entropy_summary.sh >> logs/weekly.log 2>&1
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

echo "SilentSpace Guardian — Weekly Entropy Summary"
echo "Date: $(date +%Y-%m-%d)"
echo "----------------------------------------------"

"$PY" python/generate_weekly_entropy.py

echo "----------------------------------------------"
echo "Done. Report: reports/weekly_entropy.md"
