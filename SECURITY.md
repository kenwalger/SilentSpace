# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| 0.1.x | Yes |

SilentSpace Guardian is a local-only command-line tool with no network access,
no authentication layer, no database, and no external service integrations.
Its attack surface is intentionally minimal.

---

## Threat Model

The system reads local JSON files and invokes a locally compiled COBOL binary.
The primary security concerns are therefore:

| Vector | Risk | Notes |
|---|---|---|
| Malicious meeting JSON | Low | Fields are extracted as primitives; no `eval` or shell interpolation |
| COBOL binary substitution | Medium | The binary is compiled from source in `cobol/`; do not replace it with an untrusted binary |
| Path traversal via meeting filename | Low | The file path is provided by the operator, not read from the JSON itself |
| Subprocess injection | Low | COBOL arguments are passed as a list, not via shell string interpolation |

There is no user-facing web interface, no credentials to steal, no database to
exfiltrate, and no network listener to attack.

---

## Reporting a Vulnerability

If you discover a security issue — including any scenario where supplying crafted
input could result in arbitrary code execution, unintended file access, or
privilege escalation — please report it responsibly.

**Do not open a public GitHub Issue for security vulnerabilities.**

### How to Report

1. Email: **ken.alger.778@gmail.com**
2. Subject line: `[SECURITY] SilentSpace Guardian — <brief description>`
3. Include:
   - A description of the vulnerability
   - Steps to reproduce
   - Your assessment of impact and exploitability
   - Any suggested mitigations

### Response Timeline

| Stage | Target |
|---|---|
| Acknowledgement | Within 72 hours |
| Initial assessment | Within 7 days |
| Fix or mitigation | Within 30 days (or coordinated disclosure if longer) |

You will be credited in the changelog unless you prefer to remain anonymous.

---

## Out of Scope

The following are known limitations of a demo project and are not considered
security vulnerabilities:

- The COBOL scoring formula can be trivially reverse-engineered (it is open source)
- Meeting JSON files are not encrypted at rest
- There is no audit log of which meetings were audited
- The tool does not validate that `could_be_email: true` is accurate

---

## Dependency Security

SilentSpace Guardian has **zero third-party Python dependencies**. The Python
layer uses only the standard library. The COBOL layer requires GnuCOBOL at
compile time only; the compiled binary has no runtime library dependencies
beyond the system's standard C runtime.

Keep GnuCOBOL and your Python interpreter updated through your system's
normal package manager.
