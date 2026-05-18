# Changelog

All notable changes to SilentSpace Guardian are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned

- Machine-readable output mode (`--format json`)
- `memory_context` consumed by scoring (longitudinal recurrence penalty,
  trend-aware recommendation text)
- `memory/meeting_history.json` written back after each audit
- `memory/USER.md` user preference file

---

## [0.3.7-dev] — 2026-05-18

### Changed

- **Report version string bumped from `v0.1.0` to `v0.3.0`** — The closing
  line of individual meeting reports (`audit_meeting.py`) and both footers in
  the organizational entropy report (`audit_all_meetings.py`) still referenced
  `v0.1.0`. Updated all three occurrences to `v0.3.0` to match the project's
  current development version. No scoring, output structure, or behavior
  changed.

---

## [0.3.6-dev] — 2026-05-18

### Fixed

- **`python/generate_daily_digest.py`, `generate_preflight.py`,
  `generate_weekly_entropy.py` — `load_meeting()` outside try block** — The
  `[0.3.5-dev]` fix wrapped only `audit_meeting_data()` in `try/except
  ValueError`. `load_meeting()` was still called before the try block, so a
  malformed JSON file raised `json.JSONDecodeError` (a subclass of `ValueError`)
  before the handler could catch it, aborting the entire generator run with a
  raw traceback. Fixed in all three generators by moving `load_meeting()` inside
  the try block and widening the exception tuple to `(ValueError, OSError)` so
  the handler also covers file-level I/O errors (permissions, disappearing
  files). One bad file now emits a `WARNING` to stderr and continues; valid
  files in the same run are unaffected.

- **`tests/test_generators.py` — new test file** — Added six parametrized tests
  across all three generators: two test functions × three generator scripts. A
  `bad_meeting_file` fixture writes a malformed JSON file to `meetings/` before
  each test and removes it after. Tests assert: exit code 0, `WARNING` present
  in stderr, the bad filename present in the warning, no `Traceback` in stderr.

---

## [0.3.5-dev] — 2026-05-18

### Fixed

- **`python/generate_daily_digest.py`, `generate_preflight.py`,
  `generate_weekly_entropy.py` — unhandled `ValueError` in audit loop** — Each
  generator's `main()` called `audit_meeting_data()` without an exception
  handler. A single malformed or schema-invalid JSON file in `meetings/` would
  raise `ValueError`, terminate the loop immediately with a raw Python traceback,
  and produce no report at all. Fixed in all three generators with the same
  pattern: wrap `audit_meeting_data()` in `try/except ValueError`, print a
  `WARNING: Skipping <filename>: <reason>` message to stderr, and `continue` to
  the next file. Added a post-loop guard: if no valid results were collected,
  print `ERROR: No valid meetings to process.` to stderr and exit 1 rather than
  passing an empty list to the report generator. Valid files in the same run are
  unaffected by one invalid file.

- **`tests/test_hermes_tool.py` — `_run()` had no timeout** — `subprocess.run()`
  without a timeout hangs indefinitely if the tool blocks (e.g., waiting on
  stdin when `--stdin` is specified but no data arrives, or if a subprocess it
  spawns stalls). Added `timeout=30` to the `_run()` helper. If a call exceeds
  30 seconds, `subprocess.TimeoutExpired` is raised, failing the test immediately
  with a clear diagnostic rather than blocking the suite.

---

## [0.3.4-dev] — 2026-05-18

### Fixed

- **`python/hermes_meeting_tool.py` — `--write-report` block unhandled
  `OSError`** — `generate_report()` and `save_report()` were called without
  any exception handler. If `reports/` was not writable (permission denied,
  read-only filesystem, full disk, or any other I/O condition), `save_report()`'s
  `Path.write_text()` call raised a raw `OSError` that propagated as an
  unhandled exception, printing a full Python traceback to stderr and exiting
  with code 1 by default — violating the CLI contract that all errors produce
  `ERROR: <message>` on stderr with a documented exit code. Fixed by wrapping
  the entire `--write-report` block in `try/except OSError` and routing through
  `_die(1, f"Failed to write report: {exc}")`. The `output["report_path"]`
  assignment remains outside the try block (pure Python, cannot raise). On a
  genuine write failure the tool now exits 1 and prints a clean, traceback-free
  error message.

- **`tests/test_hermes_tool.py` — no coverage for `--write-report` I/O
  failure** — Added `TestWriteReportIOError` class with two tests:
  `test_io_error_exits_nonzero` and `test_io_error_prints_clean_error`. The
  fixture `_block_report_path` creates a **directory** at the exact path
  `save_report()` would write to (`reports/hermes_io_error_fixture_report.md`,
  derived deterministically from the fixture meeting title). Attempting
  `Path.write_text()` on a directory raises `IsADirectoryError` on Linux/macOS
  and `PermissionError` on Windows — both `OSError` subclasses — triggering the
  new handler on all platforms. The fixture removes the directory after each
  test. This approach avoids making `reports/` itself read-only (which could
  corrupt the test environment if cleanup failed). Test count: 97 → 99.

---

## [0.3.3-dev] — 2026-05-18

### Fixed

- **`python/hermes_meeting_tool.py` — `report_path` was absolute** — The tool
  returned the absolute system path from `save_report()` as the `report_path`
  field in the JSON output (e.g. `C:\Users\kenal\silentspace-guardian\reports\
  weekly_alignment_sync_report.md`). Documentation examples and agent consumers
  expect a portable relative path. Fixed by importing `ROOT` from `audit_meeting`
  and emitting `report_path.relative_to(ROOT).as_posix()` — consistently
  forward-slashed and relative to the repo root on all platforms
  (e.g. `reports/weekly_alignment_sync_report.md`). Where reports are written is
  unchanged.

- **`python/generate_preflight.py` — safe-list computed via dict equality** —
  `safe = [r for r in results if r not in candidates]` used Python list
  `__contains__`, which compares full nested dicts for equality on every
  iteration. For large or subtly mutated result dicts this is fragile and
  unclear. Fixed by computing `safe` directly and independently from the same
  predicate used for `candidates`:
  `safe = [r for r in results if not _is_async_candidate(r["meeting"], r)]`.
  No dict equality, no object identity, no dependency between the two list
  comprehensions. Output is identical for the mocked dataset.

- **`skills/entropy_audit/SKILL.md` — escaped Markdown syntax** — The file
  contained `\#` for its heading and `\-` for all five bullet items, rendering
  as literal backslash-prefixed text on GitHub. Same export-artifact root cause
  as `SOUL.md`. Fixed: `\#` → `#`, five `\-` → `-`. Wording unchanged.

### Changed

- **`tests/test_hermes_tool.py` — `TestWriteReport` updated for relative
  `report_path`** — `test_write_report_file_exists` now resolves the relative
  path returned by the tool against `_ROOT` before asserting the file exists
  (`_ROOT / parsed["report_path"]`). Added `test_write_report_path_is_relative`
  which asserts `Path(parsed["report_path"]).is_absolute()` is false, locking
  in the documented output shape. Test count: 96 → 97.

---

## [0.3.2-dev] — 2026-05-18

### Fixed

- **`SOUL.md` — escaped Markdown syntax** — The file contained literal
  backslash-escaped Markdown syntax (`\#`, `\##`, `\-`) and HTML entities
  (`&#x20;`) throughout, causing headings to render as plain text prefixed with
  a backslash and list items to render as `\- item` rather than bullet points on
  GitHub and any standard Markdown renderer. Root cause: the file was exported
  from a rich-text tool that escaped Markdown metacharacters on output. Fixed by
  rewriting the file with proper Markdown syntax: `\#` → `#` (top-level heading),
  `\##` → `##` (second-level heading for "Behavioral Directives"), `\-` → `-`
  (all bullet list items), and `&#x20;` → removed (these were indentation padding
  before line-wrapped list continuations; each affected bullet is now a single
  unbroken line). All wording is preserved exactly. SOUL.md now renders cleanly
  as the authoritative Guardian persona and behavior contract.

- **`python/hermes_meeting_tool.py` — `_die()` annotated `-> None` instead of
  `-> NoReturn`** — `_die()` unconditionally calls `sys.exit()` and therefore
  never returns. Annotating it `-> None` told type checkers it could return
  normally, causing them to flag implicit `None` returns in callers like
  `_load_file()` and `_load_stdin()` — functions whose `except` branches call
  `_die()` and then fall through with no explicit return. Fixed by importing
  `NoReturn` from `typing` and changing the annotation to `-> NoReturn`. No
  runtime behavior changes.

- **`tests/test_hermes_tool.py` — `TestWriteReport` not isolated from
  `reports/`** — The three `--write-report` tests all wrote to
  `reports/weekly_alignment_sync_report.md` in the real repository directory.
  `test_write_report_file_exists` could silently pass because a stale file from
  a prior run was already present before the test invoked the tool. Added an
  `autouse` pytest fixture `_clean_report` to `TestWriteReport` that deletes the
  known report path before each test (preventing stale-file false positives) and
  again after (leaving `reports/` clean between runs). Also added an explicit
  pre-condition assertion to `test_write_report_file_exists`: the test now
  asserts the file does not exist before running the tool, making fixture failure
  immediately diagnosable. The underlying behavior — that the tool writes to
  `reports/` — is unchanged; only the test harness is isolated.

---

## [0.3.1-dev] — 2026-05-18

### Fixed

- **`python/generate_weekly_entropy.py` — threshold inconsistency** — The
  `total_weekly_hours` sum used `>= 60` to filter high-waste recurring meetings,
  while the `high_waste_recurring` list, the Overview table label
  (`Recurring Waste Score ≥ 61`), the pattern-analysis count, and the footnote
  all used `>= 61`. The off-by-one meant the hours figure counted one extra tier
  of meetings (waste == 60, i.e. the top of "Calendar Debris") that the rest of
  the report classified as below the remediation threshold. Unified to `>= 61`
  throughout — the natural boundary above the "Calendar Debris" tier (41–60).
  One line changed: `>= 60` → `>= 61` in the `total_weekly_hours` expression.

- **`python/hermes_meeting_tool.py` — unhandled `OSError` in `_load_stdin()`** —
  `sys.stdin.read()` was only wrapped in a `json.JSONDecodeError` handler. A
  broken pipe, a closed stdin descriptor, or any other I/O failure on the stdin
  stream would raise an unhandled `OSError` and produce a raw Python traceback —
  violating the CLI contract that all errors print as `ERROR: <message>` to
  stderr with a non-zero exit code. Fixed by splitting the try/except into two
  separate blocks: `OSError` on the read (exit code 1), `json.JSONDecodeError`
  on the parse (exit code 2). The fix aligns `_load_stdin()` with the existing
  two-block pattern already used in `_load_file()`.

- **`tests/test_hermes_tool.py` — unused `tmp_path` fixture in `TestWriteReport`** —
  `test_write_report_exits_zero` and `test_write_report_output_includes_report_path`
  declared `tmp_path` as a parameter but never used it. The tests write to the
  shared `reports/` directory via the tool's own `save_report()` logic — `tmp_path`
  was left over from an earlier draft. Removed the unused parameter from both
  methods.

---

## [0.3.0-dev] — 2026-05-18

### Added

- **`python/hermes_meeting_tool.py` — Hermes agent tool boundary** — Structured
  CLI interface for agent consumption. Accepts a meeting JSON from a file path
  argument or `--stdin`. Calls `audit_meeting_data()` from `audit_meeting.py`
  without duplicating any scoring logic. Outputs a structured JSON result to
  stdout containing `title`, `waste_score`, `necessity_prob`, `classification`,
  `recommendation`, and the original `meeting` dict. Supports `--write-report`
  to additionally generate a Markdown report to `reports/` using existing
  `generate_report()` and `save_report()` logic; when active, the output JSON
  includes a `report_path` key. Error handling: file not found exits 1, JSON
  parse error exits 2, meeting validation error exits 3. All errors are printed
  as `ERROR: <message>` to stderr with no Python traceback. Mutually exclusive
  source arguments (`file` / `--stdin`) are validated with a clear argparse
  error if neither or both are provided.

- **`python/generate_daily_digest.py` — Daily regret audit helper** — Audits
  all meeting JSON files in `meetings/` and writes `reports/daily_digest.md`.
  Sections: day-end summary table (meetings reviewed, average waste score,
  async candidates, high-waste count), top three priority regret targets sorted
  by waste score, and a table of all meetings flagged as async candidates
  (`could_be_email: true`). Intended for weekday 5 PM scheduling.

- **`python/generate_weekly_entropy.py` — Weekly entropy summary helper** —
  Audits all meeting files and writes `reports/weekly_entropy.md`. Focuses on
  recurring meetings: cadence, waste score, necessity probability, and estimated
  weekly person-hours lost (duration × attendees × weekly occurrences for
  meetings scoring ≥ 61). Sections: overview table, recurring meeting breakdown,
  pattern analysis (no-agenda, no-actions, could-be-email patterns in recurring
  set), and remediation priority list. Intended for Friday 4 PM scheduling.

- **`python/generate_preflight.py` — Morning preflight helper** — Audits all
  meeting files and writes `reports/preflight_report.md`. Flags meetings as
  async candidates when they meet two or more of: `could_be_email`, no agenda,
  no action items, waste score ≥ 60. Sections: preflight summary table,
  flagged meetings with their async signals listed, and cleared meetings with
  fewer than two signals. Intended for weekday 7 AM scheduling.

- **`scripts/run_daily_regret_audit.sh`** — Wrapper script for the daily
  regret audit. Detects Python (`python` or `python3`), changes to repo root,
  calls `generate_daily_digest.py`. Includes the cron entry as a header comment.
  Exits non-zero if Python is not found.

- **`scripts/run_weekly_entropy_summary.sh`** — Wrapper script for the weekly
  entropy summary. Same structure as the daily script; calls
  `generate_weekly_entropy.py`.

- **`scripts/run_preflight_audit.sh`** — Wrapper script for the morning
  preflight. Calls `generate_preflight.py`.

- **`skills/` — curated Hermes skill scaffolds** — Human-authored SKILL.md
  files for four capabilities:
  - `skills/meeting_entropy_audit/SKILL.md` — Primary tool boundary: purpose,
    full meeting JSON schema with required/optional breakdown, Python and CLI
    invocation examples, guardrails (do not modify COBOL output, validate first,
    check exit codes), and SOUL.md tone notes.
  - `skills/async_alternative_recommender/SKILL.md` — Deterministic
    recommendation lookup via `classify.py`; explains the bucket/hash selection
    mechanism, when to use the skill standalone vs. relying on the full audit
    result, and why the recommendation text is not LLM-generated.
  - `skills/summary_report_writer/SKILL.md` — Batch summary skill covering all
    three report types (summary, daily digest, weekly entropy); Python invocation
    examples for each generator function; guardrail against adding LLM narrative
    to fixed report copy.
  - `skills/cobol_output_interpreter/SKILL.md` — Documents the raw two-line
    COBOL output format, the six stdin values with expected types and ranges,
    the invariant `necessity_prob = max(5, 100 - waste_score)`, and how to call
    the binary directly for debugging.
  - `skills/README.md` — Authorship and review policy: all skills are
    human-authored, Hermes may propose but humans decide, explains why
    autonomous skill generation is not allowed, and cross-references SOUL.md
    behavioral directives with what each directive means for skill behavior.

- **`docs/hermes_integration.md`** — Architecture overview (Hermes as adaptive
  edge, Python/COBOL as stable core), both integration paths (in-process
  `audit_meeting_data()` and out-of-process CLI), full JSON output example with
  `--write-report` variant, exit code table, SOUL.md as persona contract with
  directive explanations, example Hermes prompts, and what Hermes does not do.

- **`docs/local_agent_setup.md`** — End-to-end local agent setup guide. Covers:
  GnuCOBOL installation on macOS, Ubuntu/Debian, WSL, and native Windows;
  Ollama setup (install, model pull, server start, recommended models); OpenRouter
  configuration; Anthropic API key setup; `.env` / `example.env` workflow;
  in-process Python tool registration example; out-of-process subprocess wrapper
  example; SOUL.md system prompt excerpt for agent configuration; what is real
  vs. mocked.

- **`docs/scheduled_audits.md`** — Scheduling reference for all three workflows.
  Covers the intent and output of each; manual verification commands; cron entry
  syntax with full paths and log redirection; WSL-specific cron startup notes
  including the `/etc/wsl.conf` `[boot]` command workaround; Windows Task
  Scheduler via both PowerShell (`New-ScheduledTaskAction`, `Register-ScheduledTask`)
  and GUI (step-by-step); and a reminder that the meeting files are mocked.

- **`docs/skills.md`** — Skill catalog with one-paragraph description and
  invocation example for each of the four skills; authorship policy summary;
  SOUL.md conformance table mapping each directive to what it requires of skill
  outputs.

- **`tests/test_hermes_tool.py`** — 37 subprocess tests for the Hermes tool
  boundary. Classes: `TestFileInput` (7 tests — exit 0, stdout is JSON, required
  keys present, score bounds, title match, clean stderr), `TestStdinInput` (4
  tests — same structural checks via `--stdin`), `TestErrorHandling` (9 tests —
  no args, both sources, file not found exit 1, invalid JSON exit 2 for both
  file and stdin), `TestMissingFields` (6 tests — missing title/duration/attendees
  each exit 3, empty dict exit 3, error lists all required fields),
  `TestInvalidFieldTypes` (8 tests — wrong-type title, string duration, null/string
  attendees, wrong-type boolean fields parametrized, unknown recurrence),
  `TestWriteReport` (3 tests — exit 0, `report_path` in output, file exists).
  All 37 pass. Existing 59 tests in `test_audit.py` unaffected. Total: 96 tests.

### Changed

- **All generated reports now end with a two-line closing statement** —
  `generate_report()` in `audit_meeting.py`, `generate_summary()` in
  `audit_all_meetings.py`, and all three scheduled report generators
  (`generate_daily_digest`, `generate_weekly_entropy`, `generate_preflight`)
  now append the following two lines after the existing footer tagline:

  ```
  The meeting has been remembered.
  This is not a compliment.
  ```

  This applies to all five report types: individual audit reports, the batch
  summary, the daily digest, the weekly entropy summary, and the morning
  preflight. The lines are separated from the preceding tagline by a blank line.

- **`README.md` updated to v0.3.0-dev** — Current Status updated; Hermes
  Integration section added (tool boundary, JSON output example, exit codes,
  in-process API); SOUL.md persona contract section added; Scheduled Audits
  section added (table of workflows, manual run commands); Skills section added
  (skill catalog table); Testing section updated (96 tests, two suites);
  Verification section added with all verification commands; Project Structure
  tree updated to reflect all new files.

---

## [0.2.0-dev] — 2026-05-15

### Added

- `tests/conftest.py` and `tests/test_audit.py` — pre-Hermes test suite.
  Tests the `audit_meeting_data()` agent tool boundary before any agent
  framework is wired in. Coverage: return structure (all six keys present,
  meeting dict passed through); score bounds (waste_score 0–100,
  necessity_prob 5–100); formula correctness (`necessity_prob = max(5,
  100 − waste_score)`, cap verified at 100, floor at 5); classification
  and recommendation determinism (same input → same output); input
  validation (ValueError on missing title / duration_minutes / attendees,
  error message lists all missing fields); optional field defaults
  (parametrized across has_agenda, has_action_items, could_be_email,
  recurrence, organizer, description); COBOL binary missing (monkeypatches
  binary paths and shutil.which, asserts SystemExit code 1, clears LRU
  cache before and after to avoid test pollution). Run with: pytest tests/

- `scripts/verify_demo.sh` — end-to-end demo verification script. Five
  steps: prerequisites, COBOL compilation, single meeting audit, batch
  audit, report file checks. On all passes: exit 0, "All N checks passed."
  On any failure: exit 1, failing check listed. See also: Changed below.

- `python/audit_all_meetings.py` — Batch auditor. Scores every JSON file in
  `meetings/`, writes individual Markdown reports to `reports/`, and produces
  `reports/summary_report.md` containing: total meetings audited, average waste
  score, average necessity probability, estimated weekly focus hours recovered,
  verdict breakdown by tier, top three worst offenders, most common failure mode,
  and a full meeting table sorted by waste score descending.

- `audit_meeting_data(meeting, memory_context=None) -> dict` in
  `python/audit_meeting.py` — agent-callable interface. Accepts a meeting
  dictionary, runs the full COBOL scoring pipeline, applies classification and
  recommendation logic, and returns a structured result dict with no file I/O
  and no side effects. The `memory_context` parameter is accepted but unused;
  it is the reserved placeholder for context passed in by an agent framework.
  Both CLI entry points (`audit_meeting.py`, `audit_all_meetings.py`) call this
  function internally.

- **Agent Tool Boundary section** in `docs/architecture.md` — documents
  `audit_meeting_data` as the integration point for agent frameworks, with a
  working import example and an explanation of the `memory_context` placeholder.

- `docs/memory_model.md` — planning document for persistent agent memory.
  Covers why memory is the differentiator over stateless scoring, the proposed
  `audit_history` data shape, example user preference entries, how a longitudinal
  recurrence penalty could work as a Python post-processing step (not a COBOL
  change), and an implemented-vs-planned table. Written as scaffolding,
  not specification.

- `memory/sample_meeting_history.json` — five prior-audit examples spanning
  the full outcome range: a three-audit heat death event with no structural
  improvement (Weekly Alignment Sync), a daily standup where a duration
  reduction had no scoring effect (both durations fall below the 30-minute
  threshold), a one-off post-mortem (lowest score in corpus), a maxed-out
  entropy event whose organizer has left the company (Synergy Touchpoint v3),
  and a meeting that improved by 27 points across two audits (Product Roadmap
  Brainstorm). Scaffolding only — not read by the scoring pipeline.
  All waste scores and necessity probabilities are formula-derived.

- `docs/scoring_model.md` — authoritative reference for the COBOL entropy
  engine. Documents all six inputs and two outputs, the full scoring formula
  with per-component rationale, why `waste_score` is the primary signal, why
  `necessity_prob` is currently `100 - waste_score` with a 5% floor and what
  would change that, why duration uses integer quantization, why stdin/stdout
  is intentionally simple and agent-friendly, and why the COBOL layer is
  stateless and deliberately unaware of the agent layer. Mentions "deterministic
  quantization of corporate ambiguity."

### Changed

- **`scripts/verify_demo.sh` — platform-aware cobc handling** — The prior
  version passed the "missing cobc" check on all platforms ("Python will
  auto-compile via WSL"). This was only correct on Windows/Git Bash where
  the Python wrapper provides WSL auto-compilation as a supported fallback.
  On Linux, macOS, and WSL, missing cobc is a real failure that blocks the
  pipeline. Fixed: platform is now detected at startup (MSYSTEM / OSTYPE for
  Git Bash; /proc/version for WSL; uname for macOS; Linux as default). On
  Windows, missing cobc still passes with the auto-compile note. On
  Linux/WSL, missing cobc fails with `sudo apt install gnucobol`. On macOS,
  with `brew install gnu-cobol`. PASS is not incremented for the pass-through
  note — the check passes because the fallback is real, not because the tool
  is missing. Also: meeting and report file counting now uses `find -print0`
  piped to `read -d ''` instead of glob expansion, correctly handling empty
  directories without the literal-pattern fallback. Single-audit failure
  message now explicitly says "COBOL binary not compiled" when the binary
  is absent, rather than a generic error.

- **`python/audit_meeting.py` — required-field validation in
  `audit_meeting_data()`** — The function previously used `.get()` with
  defaults for all fields, silently scoring meetings with missing
  `duration_minutes` as 60 minutes and missing `attendees` as zero. Added
  `_REQUIRED_FIELDS = ("title", "duration_minutes", "attendees")` guard:
  `ValueError` is raised listing all absent required fields if any are
  missing. Optional fields (has_agenda, has_action_items, could_be_email,
  recurrence, organizer, description) retain their defaults.

- **`ARCHITECTURE.md` restructured as a signpost** — The root file previously
  held 225 lines of Mermaid diagrams, duplicating the role of `docs/architecture.md`
  and creating ambiguity about which file was authoritative. Replaced with a
  two-sentence orientation, a three-row demo-to-production highlights table
  (Meeting input, Agent memory, Deployment), and links to `docs/architecture.md`
  and `docs/scoring_model.md`. This follows the established convention for the
  repo: uppercase root files (`README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`)
  are entry points; detailed documentation lives in `docs/`.

- **`docs/architecture.md` — Visual Diagrams section appended** — The six
  Mermaid diagrams removed from the root `ARCHITECTURE.md` are preserved here
  as a new section at the end of the file: high-level system overview, detailed
  data flow, scoring pipeline sequence, COBOL scoring decision tree,
  classification tiers, and module dependency map. The `memory_contxt` typo in
  the Road to Production table was corrected to `memory_context`.

- **`audit_meeting.py` — `main()` delegates to `audit_meeting_data()`** —
  Scoring, classification, and recommendation logic are no longer duplicated in
  `main()`. The function calls `audit_meeting_data()` and unpacks the result
  dict for console output and report generation.

- **`audit_all_meetings.py` — simplified via `audit_meeting_data()`** —
  `audit_all()` no longer takes `bin_path` and `wsl_prefix` as parameters.
  Binary resolution is now internal to `audit_meeting_data()`. Removed
  `ensure_cobol_binary`, `score_meeting` from imports; removed the `classify`
  import entirely (`classify_meeting` and `async_recommendation` are now
  encapsulated inside `audit_meeting_data()`).

- **`ensure_cobol_binary()` cached with `@functools.lru_cache(maxsize=1)`** —
  The WSL distro probe (a subprocess call) now runs at most once per process.
  In a 12-meeting batch, this reduces WSL subprocess probes from 12 to 1.

- **`reports/summary_report.md` tone** — Rewritten to read as a boring
  enterprise dashboard authored by someone quietly losing faith in
  organizational life. Renamed sections: **Organizational Entropy Report**
  (header with Period Assessed, Prepared by, Distribution), **Calendar Damage
  Assessment** (metrics table), **Entropy Distribution by Classification**
  (adds Share % column), **Priority Remediation Targets** (top 3 with
  recommended remediation action), **Root Cause Summary** (dry prose),
  **Full Asset Register** (all meetings). Three new indicators added to the
  metrics table: **Meetings Spiritually Async** (could be email), **Corporate
  Heat Death Events** (waste ≥ 81), **Executive Visibility Rituals** (no
  agenda, no action items, more than three attendees). Footer: *"No meeting
  was held to review this report."*

### Fixed

- **`python/audit_meeting.py` — `main()` exposes raw traceback on invalid
  input** — If the meeting JSON was missing required fields, `audit_meeting_data()`
  raised `ValueError` and `main()` had no handler, producing a raw Python
  traceback on stderr. Added `try/except ValueError` around the
  `audit_meeting_data()` call in `main()`: prints `ERROR: <message>` to
  stderr and exits with code 1. Normal successful runs are unchanged.

- **`python/audit_meeting.py` — `score_meeting()` inconsistent with
  required-field validation** — `score_meeting()` used `.get("duration_minutes",
  60)` and `.get("attendees", [])` with silent fallback defaults for fields
  that `audit_meeting_data()` now guarantees are present. Since
  `score_meeting()` is only reachable after validation passes, the defaults
  were both unreachable and misleading. Replaced with direct key access
  (`meeting["duration_minutes"]`, `meeting["attendees"]`); added a docstring
  note that the function assumes pre-validated input. Optional fields
  (`has_agenda`, `has_action_items`, `could_be_email`, `recurrence`) retain
  their `.get()` defaults unchanged.

- **`tests/test_audit.py` — unused `import shutil`** — `shutil` was imported
  at module level but never used directly; the binary-missing mock references
  `audit_meeting.shutil`, not the local name. Removed.

- **`tests/test_audit.py` — no CLI error-handling coverage** — Added
  `TestCliErrorHandling` (3 tests): invokes `audit_meeting.py` as a subprocess
  with a JSON file missing `duration_minutes` and `attendees`; asserts exit
  code 1, no `Traceback` in stderr, and that the error message names both
  missing fields. Validation fires before `ensure_cobol_binary()` is reached,
  so the tests do not require a compiled COBOL binary. Module docstring updated
  to reflect that 2 of 33 tests (not 1 of 30) do not require `cobc`.

- **`docs/architecture.md` — Python Layer description stale** — Responsibility
  list did not reflect required-field validation, direct key access in
  `score_meeting()`, or the `ValueError` → clean error path in `main()`.
  Updated items 3, 4, and 7 (renumbered to 7 from the original 7); item 7
  (CLI error handling) added as a new entry.

- **`scripts/verify_demo.sh` unquoted `$PY` variable** — The Python
  interpreter variable was used unquoted in three places: the version
  check (`$($PY --version 2>&1)`), the single-audit invocation
  (`$PY python/audit_meeting.py ...`), and the batch-audit invocation
  (`$PY python/audit_all_meetings.py ...`). An unquoted variable
  undergoes word splitting and glob expansion, causing silent failure
  when the interpreter path contains spaces (e.g. a user-local pyenv
  or virtualenv path). All three occurrences replaced with `"$PY"`.

- **`README.md` missing COBOL prerequisite for `pytest`** — The Run
  Tests section did not mention that most tests require the COBOL
  entropy engine. Added a prerequisite note: GnuCOBOL (`cobc`) must
  be installed, or the compiled binary must already exist. The Python
  wrapper auto-compiles on first use. Added a clarifying sentence that
  only `TestCobolBinaryMissing` deliberately exercises the failure path
  and does not require `cobc`. Simplified the celery workaround sentence
  slightly.

- **`tests/test_audit.py` missing runtime dependency note** — The
  module docstring described what the tests cover but did not warn that
  29 of 30 tests invoke the real COBOL binary. Added a "Runtime
  dependency" paragraph naming the exception (`TestCobolBinaryMissing`)
  and explaining that the wrapper compiles automatically on a clean run
  if `cobc` is available.

- **`tests/test_audit.py` formula comment for `_HIGH_WASTE`** — The inline
  comment stated the attendee penalty as 30 (the cap), but the correct value
  for 15 attendees is `min(30, (15−3)×2) = 24`. The cap of 30 is only
  reached at 18 or more attendees. Corrected formula total: 20+24+18+15+15+10+20
  = 122, capped at 100. The assertion (`waste_score == 100`) was already correct
  and is unchanged.

- **`python/audit_meeting.py` unreachable default in `audit_meeting_data()`** —
  The return statement used `meeting.get("title", "Untitled Meeting")`. Since
  `_REQUIRED_FIELDS` validation raises `ValueError` before reaching the return
  if `"title"` is absent, the default was dead code. Replaced with direct access
  `meeting["title"]`.

- **`README.md` missing pytest workaround** — A globally-installed celery pytest
  plugin (incompatible with Python 3.12) crashes collection with
  `ImportError: cannot import name 'formatargspec'`. The README now documents
  `pytest tests/ -p no:celery` as a fallback. The plugin does not affect test
  behavior; the flag simply suppresses its broken initialisation.

- **`dict | None` annotation raises minimum Python version to 3.10** —
  `audit_meeting_data()` used the `X | Y` union syntax (PEP 604) introduced
  in Python 3.10. The project previously required only Python 3.9. Fixed by
  replacing `dict | None` with `Optional[dict]` from `typing`, which is valid
  from Python 3.5 onward.

- **Formula-inconsistent scores in `memory/sample_meeting_history.json`** —
  Three entries had hand-written scores that diverged from the COBOL formula
  by up to 12 points. Since this file is intended as reference data for future
  longitudinal scoring logic, the errors could misdirect that implementation.
  All scores are now derived from the formula.
  Corrections:
  — Weekly Alignment Sync audit-1: `necessity_prob` 4 → 5
    (`max(5, 100-96)` = 5, not 4)
  — Daily Engineering Standup audit-1: `waste_score` 65 → 63,
    `necessity_prob` 35 → 37
  — Daily Engineering Standup audit-2: `waste_score` 60 → 63,
    `necessity_prob` 40 → 37 (duration 30→15 min has no scoring effect;
    the duration drag penalty only triggers above 30 minutes, so both
    historical snapshots score identically — the duration cut was not
    the reform the notes implied)
  — Product Roadmap Brainstorm audit-1: `waste_score` 50 → 62,
    `necessity_prob` 50 → 38 (classification corrected from Calendar
    Debris to Meeting-Shaped Void; reform narrative updated to reflect
    a 27-point improvement, not 15)

- **Windows console encoding** — Classification labels contain an em-dash that
  CP1252/CP437 terminals can't display, producing garbage output. Fixed by
  calling `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` at
  startup in both `audit_meeting.py` and `audit_all_meetings.py` when running
  on Windows. Report files were already written with explicit `encoding="utf-8"`
  and were unaffected.

- **Slug collapse on punctuation** (`1:1` → `11`) — `save_report()` stripped
  punctuation before converting whitespace to underscores. Colons adjacent to
  digits were removed silently, merging tokens: `1:1` → `11`. Fixed by
  replacing non-word characters with a space instead of deleting them, so
  `1:1 Manager Check-In` → `1_1_manager_check_in_report.md`.

- **Windows path separator in console output** — `Report saved to:` printed a
  backslash-separated Windows path. Fixed by calling `.as_posix()` so output
  is consistently forward-slash on all platforms.

- **`CLAUDE.md` incorrect interface description** — Key Workflow step 3 stated
  the COBOL binary received parameters as "CLI args". COBOL Notes section stated
  it "Accepts 6 positional CLI arguments". The binary reads from stdin. Both
  corrected to reflect the actual interface.

- **`docs/architecture.md` stale interface descriptions** — Data flow diagram
  showed CLI-arg invocation syntax. The Input section was titled "Positional CLI
  Arguments". The Python Layer description said "6 positional arguments". All
  three corrected to reflect the stdin interface. Agent Tool Boundary import
  example corrected: `from python.audit_meeting import ...` raised
  `ModuleNotFoundError` because `audit_meeting.py` imports `classify` from
  its own directory; corrected to include `sys.path.insert(0, "python")`.

- **`docs/architecture.md` stale sequence diagram label** — Diagram 3 showed
  the short `classify.py` return value without the em-dash subheading:
  `"Corporate Heat Death Event: Entropy Made Flesh"`. Corrected to the full
  string: `"Corporate Heat Death Event: Entropy Made Flesh — This meeting is
  why people quit."` Trailing newline also added to end of file.

- **`python/audit_meeting.py` — `audit_meeting_data()` docstring Raises clause
  stale** — After `_validate_meeting()` was extracted, the `Raises:` section
  still said "if any field in `_REQUIRED_FIELDS` is absent", which described
  only the old presence check. Updated to describe the full scope: absent, wrong
  type, or invalid value; collects all errors before raising via
  `_validate_meeting()`.

- **`scripts/verify_demo.sh` — cobc stderr suppressed on compilation failure** —
  The `cobc` invocation used `2>/dev/null`, discarding compiler output even when
  compilation failed. The script reported "cobc compilation failed" but gave no
  diagnostic detail. Removed `2>/dev/null` so compiler errors print to the
  terminal and the failure check above can cite them.

- **`tests/test_audit.py` — `_MEETING_FILES` empty list silently skips
  parametrized suite** — If `meetings/*.json` matched nothing (missing directory,
  wrong working directory, accidental deletion), `pytest.mark.parametrize` would
  collect zero cases and report 0 passed with no warning. Added a module-level
  guard: raises `RuntimeError` at collection time if `_MEETING_FILES` is empty,
  making the failure loud and immediately diagnosable.

- **`docs/windows-wsl-setup.md` outdated "Audit All" section** — Referenced a
  manual shell loop (`for f in meetings/*.json; do ...`) that predates
  `audit_all_meetings.py`. Replaced with `python3 python/audit_all_meetings.py`.

- **`example.env` undocumented gap** — Listed environment variables
  (`COBOL_BINARY_PATH`, `REPORTS_DIR`, `GUARDIAN_DEBUG`) as if they were active.
  None are currently read by the Python scripts. Added "Planned" notes to each
  variable so the file accurately describes their status.

- **`python/audit_meeting.py` — validation accepts `{"attendees": null}`** —
  `_REQUIRED_FIELDS` presence check confirmed the key existed but did not inspect
  the value. A meeting like `{"attendees": null}` passed validation, then caused
  an unhandled `TypeError` (`len(None)`) inside `score_meeting()`, producing a
  raw traceback in the CLI — exactly the failure mode that the `ValueError` catch
  was meant to prevent. Fixed by extracting `_validate_meeting(meeting)` with
  full type and shape checks: `title` must be a non-empty string; `duration_minutes`
  must be a positive integer (bool excluded, since `bool` is a subclass of `int`);
  `attendees` must be a non-empty list; optional boolean fields must be `bool` if
  present; `recurrence` must be a known level if present. All errors are collected
  before raising so the caller sees the full problem list in one `ValueError`.
  `audit_meeting_data()` now calls `_validate_meeting()` instead of the inline
  presence-only check. The `main()` try/except is expanded to also wrap
  `load_meeting()` and covers `OSError` so file-not-found errors also produce a
  clean `ERROR:` message instead of a traceback.

- **`tests/test_audit.py` — insufficient type/shape coverage** — `TestInputValidation`
  previously tested only missing-field presence (3 cases) and optional-field
  defaults (6 parametrized cases). Added 15 new type/shape tests: empty and
  whitespace-only title, wrong-type title; `None`, string, zero, negative, and
  `bool` duration; `None`, wrong-type, and empty-list attendees; wrong-type
  optional booleans (3 parametrized); unknown recurrence string. Consolidated
  `TestCliErrorHandling` from 3 separate subprocess invocations (same file, same
  command, three assertions) into 1 combined test, and added a second CLI test
  for `{"attendees": null}` to exercise the new type validation through the
  real entry point. Added `TestRealMeetingFiles`: parametrized over all 12
  committed meeting JSON files, calls `_validate_meeting()` directly (no COBOL
  binary required), verifies that every shipped fixture passes the new schema
  rules. Test total: 33 → 59. Tests not requiring the COBOL binary: 2 → 34.

- **`docs/architecture.md` — Python Layer description stale** — Responsibility
  list did not reflect `_validate_meeting()` or the expanded error scope in
  `main()`. Item 3 (agent interface) now mentions delegation to `_validate_meeting()`.
  Item 4 is a new entry documenting `_validate_meeting()` type/shape rules.
  Remaining items renumbered (5–11). Item 8 (formerly item 7, CLI error handling)
  updated to mention `OSError` coverage and `load_meeting()` scope.

---

## [0.1.0] — 2026-05-15

### Added

#### Core Pipeline
- `python/audit_meeting.py` — Entry point. Loads a meeting JSON, extracts
  six scoring parameters, pipes them to the COBOL entropy engine via stdin,
  classifies the result, prints a console summary, and writes a Markdown
  report to `reports/`. Auto-compiles the COBOL binary on first run using
  native `cobc` if available, or WSL (Ubuntu/Debian) on Windows as a fallback.
- `python/classify.py` — Pure classification functions. Maps waste scores
  to five labeled tiers. Generates deterministic async recommendations
  derived from the meeting title hash (same input always yields same output).
- `cobol/entropy_engine.cob` — GnuCOBOL fixed-format scoring algorithm.
  Reads six scoring parameters from stdin, one per line. Outputs waste score
  and necessity probability as two integers on separate stdout lines.

#### Meeting Data (12 files)
- `meetings/weekly_alignment_sync.json` — Score: 92. The meeting that
  started in Q3 2019 and outlived the team that created it.
- `meetings/daily_standup.json` — Score: 60. Nominally 15 minutes.
- `meetings/quarterly_business_review.json` — Score: 53. Necessary.
  Expensive. Both.
- `meetings/cross_functional_deep_dive.json` — Score: 81. All stakeholders.
  No agenda. Synergy pending.
- `meetings/status_update_roundtable.json` — Score: 96. Eight people
  reading a spreadsheet aloud.
- `meetings/executive_all_hands.json` — Score: ~71. The deck was emailed
  Friday. The Q&A was cut short due to time.
- `meetings/product_roadmap_brainstorm.json` — Score: 35. Has an agenda.
  Has action items. An outlier.
- `meetings/incident_postmortem.json` — Score: 28. Four people. A timeline.
  The closest thing to a genuinely necessary meeting in the corpus.
- `meetings/one_on_one_check_in.json` — Score: 30. Two people. Biweekly.
  The guardian is suspicious but cannot fault it.
- `meetings/offsite_planning_session.json` — Score: ~85. Four hours.
  Twelve people. One whiteboard. Outcomes summarized in a deck never opened.
- `meetings/lunch_and_learn.json` — Score: ~55. Optional and catered.
  The entropy engine is uncertain what to do with this one.
- `meetings/synergy_touchpoint_v3.json` — Score: 100. Third iteration of
  a meeting that should not have had a first. Organizer has left the company.

#### Documentation
- `README.md` — Project overview, prerequisites, quick start, classification
  table, and project layout.
- `CLAUDE.md` — Claude Code operational guide: JSON schema, COBOL interface,
  scoring formula, tone rules, and explicit out-of-scope list.
- `ARCHITECTURE.md` — Visual system architecture with Mermaid.js diagrams:
  high-level overview, detailed data flow, sequence diagram, COBOL scoring
  decision tree, classification tier graph, and module dependency map.
- `docs/architecture.md` — Detailed prose architecture: input parameters,
  scoring formula, output format, layer responsibilities, JSON schema,
  classification table, and constraint rationale.
- `docs/windows-wsl-setup.md` — Beginner-friendly Windows setup guide
  covering WSL2 installation, Ubuntu configuration, Python and GnuCOBOL
  installation, manual compilation, and a full first-run walkthrough with
  expected output and a troubleshooting section.

#### Open Source Governance
- `LICENSE.md` — MIT License.
- `CONTRIBUTING.md` — Contribution guide covering meeting JSON, COBOL
  modifications, Python changes, and pull request process.
- `SECURITY.md` — Vulnerability reporting policy and scope definition.
- `CODE_OF_CONDUCT.md` — Contributor Covenant 2.1.

#### Infrastructure
- `.gitignore` — Excludes `.env`, compiled COBOL binaries, generated
  reports (`reports/*.md`), Python cache, and standard IDE/OS noise.
  `reports/.gitkeep` remains tracked; report files do not.
- `.env` — Gitignored local environment file. All variables commented out;
  defaults apply without it.
- `example.env` — Committed reference listing all supported environment
  variables (`COBOL_BINARY_PATH`, `REPORTS_DIR`, `GUARDIAN_DEBUG`) with
  descriptions and default values.
- `reports/.gitkeep` — Placeholder to track the output directory in git
  without committing generated report files.

### Fixed

- **Second-run failure on Windows** — `ensure_cobol_binary()` previously
  returned a bare `COBOL_BIN` path with `use_wsl=False` whenever the binary
  existed on disk, regardless of platform. On Windows the binary is a Linux
  ELF compiled by WSL; attempting to execute it natively fails silently on
  the first invocation and loudly on every subsequent one. Fixed by checking
  `sys.platform == "win32"` when the binary is found and routing execution
  back through WSL.
- **WSL distro probed twice per invocation** — `_wsl_distro()` was called
  independently during compilation and again during execution, each spawning
  a `wsl --which cobc` subprocess. Consolidated into a single
  `_get_wsl_prefix()` call whose result is threaded through to `score_meeting()`.
- **Classification computed redundantly** — `classify_meeting()` and
  `async_recommendation()` were each called twice: once in `main()` for
  console output and again inside `generate_report()`. Both functions now
  receive the pre-computed values as arguments.

### Changed

- `_compile_native()` and `_compile_wsl()` merged into `_compile(wsl_prefix)`.
  Empty prefix means native; non-empty means WSL. One function instead of two.
- `ensure_cobol_binary()` return type changed from `tuple[Path, bool]` to
  `tuple[Path, list[str]]`. The WSL command prefix is now concrete and
  reusable rather than a flag that callers had to re-derive.

---

[Unreleased]: https://github.com/kenwalger/silentspace-guardian/commits/main
[0.2.0-dev]: https://github.com/kenwalger/silentspace-guardian/compare/8f340da...main
[0.1.0]: https://github.com/kenwalger/silentspace-guardian/commit/8f340da
