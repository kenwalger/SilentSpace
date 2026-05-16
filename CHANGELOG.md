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

## [0.2.0-dev] — 2026-05-15

### Added

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

- **`docs/windows-wsl-setup.md` outdated "Audit All" section** — Referenced a
  manual shell loop (`for f in meetings/*.json; do ...`) that predates
  `audit_all_meetings.py`. Replaced with `python3 python/audit_all_meetings.py`.

- **`example.env` undocumented gap** — Listed environment variables
  (`COBOL_BINARY_PATH`, `REPORTS_DIR`, `GUARDIAN_DEBUG`) as if they were active.
  None are currently read by the Python scripts. Added "Planned" notes to each
  variable so the file accurately describes their status.

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

[Unreleased]: https://github.com/kenwalger/silentspace-guardian/compare/v0.2.0-dev...HEAD
[0.2.0-dev]: https://github.com/kenwalger/silentspace-guardian/compare/v0.1.0...v0.2.0-dev
[0.1.0]: https://github.com/kenwalger/silentspace-guardian/releases/tag/v0.1.0
