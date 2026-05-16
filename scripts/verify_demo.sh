#!/usr/bin/env bash
# End-to-end demo verification for SilentSpace Guardian.
# On Windows, run from Git Bash or WSL.
# Usage:  bash scripts/verify_demo.sh

cd "$(dirname "$0")/.."

PASS=0
FAIL=0

ok()   { printf "  [PASS] %s\n" "$*"; PASS=$((PASS + 1)); }
fail() { printf "  [FAIL] %s\n" "$*"; FAIL=$((FAIL + 1)); }

# Detect Python interpreter (python or python3)
PY=""
for cmd in python python3; do
    command -v "$cmd" >/dev/null 2>&1 && PY="$cmd" && break
done

printf "\nSilentSpace Guardian -- Demo Verification\n"
printf "==========================================\n\n"

# ── 1. Prerequisites ─────────────────────────────────────────────────────────
printf "1. Prerequisites\n"

if [[ -n "$PY" ]]; then
    ok "Python: $($PY --version 2>&1)"
else
    fail "Python not found -- install Python 3.9+ and add it to PATH"
fi

if [[ -f "cobol/entropy_engine.cob" ]]; then
    ok "COBOL source: cobol/entropy_engine.cob"
else
    fail "COBOL source missing: cobol/entropy_engine.cob"
fi

MEETING_COUNT=$(ls meetings/*.json 2>/dev/null | wc -l | tr -d ' ')
if [[ "$MEETING_COUNT" -gt 0 ]]; then
    ok "$MEETING_COUNT meeting JSON files in meetings/"
else
    fail "No meeting JSON files found in meetings/"
fi

printf "\n"

# ── 2. COBOL compilation ──────────────────────────────────────────────────────
printf "2. COBOL compilation\n"

if command -v cobc >/dev/null 2>&1; then
    if cobc -x -o cobol/entropy_engine cobol/entropy_engine.cob 2>/dev/null; then
        ok "Compiled: cobol/entropy_engine (native cobc)"
    else
        fail "cobc compilation failed -- check cobol/entropy_engine.cob"
    fi
else
    ok "cobc not on PATH -- Python will auto-compile via WSL on Windows"
fi

printf "\n"

# ── 3. Single meeting audit ───────────────────────────────────────────────────
printf "3. Single meeting audit\n"
printf "   Meeting: meetings/weekly_alignment_sync.json\n"
printf "   ----------------------------------------------------------\n"

if [[ -n "$PY" ]]; then
    if $PY python/audit_meeting.py meetings/weekly_alignment_sync.json; then
        ok "Single audit completed"
    else
        fail "audit_meeting.py exited with error"
    fi
else
    fail "Skipped -- Python not found"
fi

printf "\n"

# ── 4. Batch audit ────────────────────────────────────────────────────────────
printf "4. Batch audit (all meetings, output suppressed)\n"

if [[ -n "$PY" ]]; then
    if $PY python/audit_all_meetings.py >/dev/null 2>&1; then
        ok "All $MEETING_COUNT meetings scored"
    else
        fail "audit_all_meetings.py failed -- rerun without >/dev/null to debug:"
        printf "       %s python/audit_all_meetings.py\n" "$PY"
    fi
else
    fail "Skipped -- Python not found"
fi

printf "\n"

# ── 5. Report files ───────────────────────────────────────────────────────────
printf "5. Report files\n"

if [[ -f "reports/summary_report.md" ]]; then
    ok "reports/summary_report.md present"
else
    fail "reports/summary_report.md missing"
fi

count=0
for f in reports/*_report.md; do
    [[ -f "$f" && "$f" != "reports/summary_report.md" ]] && count=$((count + 1))
done

if [[ "$count" -gt 0 ]]; then
    ok "$count individual report(s) in reports/"
else
    fail "No individual reports found in reports/"
fi

printf "\n"

# ── Result ────────────────────────────────────────────────────────────────────
printf "==========================================\n"
if [[ "$FAIL" -eq 0 ]]; then
    printf "All %d checks passed. The demo is ready.\n\n" "$PASS"
else
    printf "%d of %d checks failed.\n" "$FAIL" "$((PASS + FAIL))"
    printf "Resolve the issues above before presenting the demo.\n\n"
    exit 1
fi
