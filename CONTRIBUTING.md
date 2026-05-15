# Contributing to SilentSpace Guardian

Thank you for wanting to help protect the world's calendars.

This is a demo project with a narrow, intentional scope. Contributions that stay
within that scope are very welcome. Contributions that add OAuth, a database, or
a Kubernetes helm chart will be declined with a humorous but firm rejection notice.

---

## What We Welcome

- **New meeting JSON files** — the corpus is always hungry for fresh corporate tragedy
- **Improvements to the COBOL scoring formula** — new penalty categories, rebalanced weights
- **Python layer improvements** — cleaner output, better error messages, new report fields
- **Documentation fixes** — typos, clarity, Mermaid diagram corrections
- **Bug reports** — especially COBOL compilation issues across different GnuCOBOL versions

## What We Are Not Accepting (Yet)

- Calendar, Slack, or any external service integration
- Web application, REST API, or database layer
- Docker or container configuration
- OAuth or any authentication mechanism
- Third-party Python dependencies

---

## Getting Started

### Prerequisites

- Python 3.9+
- GnuCOBOL (`cobc`)
  - macOS: `brew install gnu-cobol`
  - Ubuntu/Debian: `sudo apt install gnucobol`
  - Windows: use WSL with the above

### Setup

```bash
git clone https://github.com/kenwalger/silentspace-guardian.git
cd silentspace-guardian

# Verify the pipeline works end-to-end
python python/audit_meeting.py meetings/weekly_alignment_sync.json
```

There are no Python dependencies to install. The COBOL binary compiles automatically.

---

## Adding a New Meeting File

1. Create `meetings/<descriptive_slug>.json`
2. Follow the required schema exactly:

```json
{
  "title": "string",
  "recurrence": "none | monthly | biweekly | weekly | daily",
  "duration_minutes": 60,
  "attendees": ["Name or Role"],
  "has_agenda": false,
  "has_action_items": false,
  "could_be_email": true,
  "organizer": "name or email",
  "description": "One sentence of dry flavor text."
}
```

3. Verify it audits cleanly:
   ```bash
   python python/audit_meeting.py meetings/<your_file>.json
   ```

4. The description field should be satirical but not mean-spirited toward any
   real individual or group. Skewer the institution, not the person.

---

## Modifying the COBOL Scoring Engine

The scoring formula lives in `cobol/entropy_engine.cob`. It uses GnuCOBOL
fixed-format syntax (columns matter — see `docs/architecture.md`).

After any change:

```bash
# Delete the cached binary to force recompilation
rm -f cobol/entropy_engine cobol/entropy_engine.exe

# Re-run any meeting to verify the output format is still intact
python python/audit_meeting.py meetings/incident_postmortem.json
```

The output must remain exactly two integers on separate stdout lines.
Do not change this contract without also updating `audit_meeting.py`.

If you add a new scoring parameter, you must also:
- Add it to the CLI argument list in `entropy_engine.cob`
- Add it to the parameter extraction in `audit_meeting.py`
- Document it in `docs/architecture.md` and `ARCHITECTURE.md`

---

## Modifying the Python Layer

- `python/audit_meeting.py` — keep changes focused on orchestration and output
- `python/classify.py` — classification thresholds and recommendation text

Both files use only the Python standard library. Do not add `import` statements
for third-party packages.

Run a quick sanity check after any Python change:
```bash
python -c "import ast; ast.parse(open('python/audit_meeting.py').read()); print('OK')"
python -c "import ast; ast.parse(open('python/classify.py').read()); print('OK')"
```

---

## Pull Request Guidelines

1. **One logical change per PR.** A new meeting file is one PR. A scoring formula
   adjustment is a separate PR. Do not bundle unrelated changes.

2. **Test your change end-to-end** by running at least one full audit before opening a PR:
   ```bash
   python python/audit_meeting.py meetings/weekly_alignment_sync.json
   ```

3. **Update the CHANGELOG.** Add your change under `## [Unreleased]` following the
   existing format.

4. **Keep the tone.** Dry enterprise satire. Factual code. Absurd copy.

---

## Reporting Bugs

Open a GitHub Issue with:
- Your OS and GnuCOBOL version (`cobc --version`)
- Your Python version (`python --version`)
- The exact command you ran
- The full error output

---

## Code of Conduct

All contributors are expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
