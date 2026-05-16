# SilentSpace Guardian — Architecture

SilentSpace Guardian is a three-layer pipeline: meeting JSON flows into a Python orchestration layer, which pipes six parameters to a compiled COBOL entropy engine, which returns a waste score and necessity probability that drive classification and Markdown report generation. The agent interface (`audit_meeting_data`) sits at the Python layer boundary; nothing above it touches COBOL directly.

There are no external services, no databases, and no network calls in the current version. The entire system runs locally.

| Dimension | Demo (v0.1.0) | Production Path |
|---|---|---|
| Meeting input | Mocked JSON files | Google Calendar / Outlook via OAuth 2.0 |
| Agent memory | `memory_context` placeholder | Live context from prior audit history and user preferences |
| Deployment | Local only | $5 VPS, systemd service, or serverless function |

For visual diagrams, JSON schema, agent tool boundary, classification tiers, and full constraints, see [docs/architecture.md](docs/architecture.md).
For the COBOL scoring formula, input/output specification, and engine rationale, see [docs/scoring_model.md](docs/scoring_model.md).
