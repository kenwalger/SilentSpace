#!/usr/bin/env bash
# End-to-end demo verification for SilentSpace Guardian.
# Usage:  bash scripts/verify_demo.sh
# Windows: run from Git Bash (MSYSTEM set) or WSL.

cd "$(dirname "$0")/.."

PASS=0
FAIL=0

ok()   { printf "  [PASS] %s\n" "$*"; PASS=$((PASS + 1)); }
fail() { printf "  [FAIL] %s\n" "$*"; FAIL=$((FAIL + 1)); }

# ── Platform detection ────────────────────────────────────────────────────────
# MSYSTEM is set by Git Bash (MINGW64, MSYS2, etc.).
# OSTYPE is set by bash: "msys" / "cygwin" for Windows-ish shells.
# /proc/version containing "microsoft" distinguishes WSL from native Linux.
if [[ -n "${MSYSTEM:-}" ]] || [[ "${OSTYPE:-}" == "msys" ]] || [[ "${OSTYPE:-}" == "cygwin" ]]; then
    PLATFORM="windows"
elif [[ -f /proc/version ]] && grep -qi microsoft /proc/version 2>/dev/null; then
    PLATFORM="wsl"
elif [[ "$(uname -s 2>/dev/null)" == "Darwin" ]]; then
    PLATFORM="macos"
else
    PLATFORM="linux"
fi

# ── Python detection ──────────────────────────────────────────────────────────
PY=""
for cmd in python python3; do
    command -v "$cmd" >/dev/null 2>&1 && PY="$cmd" && break
done

printf "\nSilentSpace Guardian -- Demo Verification\n"
printf "==========================================\n"
printf "  Platform: %s\n\n" "$PLATFORM"

# ── 1. Prerequisites ──────────────────────────────────────────────────────────
printf "1. Prerequisites\n"

if [[ -n "$PY" ]]; then
    ok "Python: $("$PY" --version 2>&1)"
else
    fail "Python not found -- install Python 3.9+ and add it to PATH"
fi

if [[ -f "cobol/entropy_engine.cob" ]]; then
    ok "COBOL source: cobol/entropy_engine.cob"
else
    fail "COBOL source missing: cobol/entropy_engine.cob"
fi

# Count meeting JSON files without glob expansion (handles empty dir cleanly)
MEETING_COUNT=0
if [[ -d "meetings" ]]; then
    while IFS= read -r -d '' _f; do
        MEETING_COUNT=$((MEETING_COUNT + 1))
    done < <(find meetings -maxdepth 1 -name "*.json" -print0 2>/dev/null)
fi

if [[ "$MEETING_COUNT" -gt 0 ]]; then
    ok "$MEETING_COUNT meeting JSON file(s) in meetings/"
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
elif [[ "$PLATFORM" == "windows" ]]; then
    # On Windows/Git Bash, cobc is not available natively. The Python wrapper
    # detects WSL and compiles via it on first invocation. Supported path.
    ok "cobc not on native PATH -- Python will auto-compile via WSL (Windows)"
elif [[ "$PLATFORM" == "macos" ]]; then
    fail "GnuCOBOL not found. Install with: brew install gnu-cobol"
else
    # Linux and WSL: cobc must be present. WSL has apt; native Linux likewise.
    fail "GnuCOBOL not found. Install with: sudo apt install gnucobol"
fi

printf "\n"

# ── 3. Single meeting audit ───────────────────────────────────────────────────
printf "3. Single meeting audit\n"
printf "   Meeting: meetings/weekly_alignment_sync.json\n"
printf "   ----------------------------------------------------------\n"

if [[ -n "$PY" ]]; then
    if "$PY" python/audit_meeting.py meetings/weekly_alignment_sync.json; then
        ok "Single audit completed"
    else
        if [[ ! -f "cobol/entropy_engine" && ! -f "cobol/entropy_engine.exe" ]]; then
            fail "Single audit failed -- COBOL binary not compiled (see step 2)"
        else
            fail "audit_meeting.py failed -- check stderr above"
        fi
    fi
else
    fail "Skipped -- Python not found"
fi

printf "\n"

# ── 4. Batch audit ────────────────────────────────────────────────────────────
printf "4. Batch audit (all meetings, output suppressed)\n"

if [[ -n "$PY" ]]; then
    if "$PY" python/audit_all_meetings.py >/dev/null 2>&1; then
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

# Count individual reports without glob expansion
report_count=0
if [[ -d "reports" ]]; then
    while IFS= read -r -d '' f; do
        [[ "$(basename "$f")" != "summary_report.md" ]] && report_count=$((report_count + 1))
    done < <(find reports -maxdepth 1 -name "*_report.md" -print0 2>/dev/null)
fi

if [[ "$report_count" -gt 0 ]]; then
    ok "$report_count individual report(s) in reports/"
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
