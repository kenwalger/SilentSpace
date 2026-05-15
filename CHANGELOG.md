# Changelog

All notable changes to SilentSpace Guardian are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- CLI flag `--all` to audit every file in `meetings/` in a single pass
- Summary report aggregating scores across all audited meetings
- Machine-readable output mode (`--format json`)

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
- `ARCHITECTURE.md` — Visual system architecture with five Mermaid.js diagrams:
  high-level overview, detailed data flow, sequence diagram, COBOL scoring
  decision tree, and classification tier graph.
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

[Unreleased]: https://github.com/kenwalger/silentspace-guardian/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/kenwalger/silentspace-guardian/releases/tag/v0.1.0
