#!/usr/bin/env bash
# SilentSpace Guardian — Morning Calendar Preflight
#
# Intended schedule: weekday mornings at 07:00 (7 AM local time)
# Output:           reports/preflight_report.md
#
# Usage:
#   bash scripts/run_preflight_audit.sh
#
# Manual verification:
#   bash scripts/run_preflight_audit.sh && cat reports/preflight_report.md
#
# Cron entry (Linux/macOS/WSL):
#   0 7 * * 1-5  cd /path/to/silentspace-guardian && bash scripts/run_preflight_audit.sh >> logs/preflight.log 2>&1
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

echo "SilentSpace Guardian — Morning Preflight"
echo "Date: $(date +%Y-%m-%d)"
echo "-----------------------------------------"

"$PY" python/generate_preflight.py

echo "-----------------------------------------"
echo "Done. Report: reports/preflight_report.md"
