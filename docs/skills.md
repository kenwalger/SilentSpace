# Skills

SilentSpace Guardian skills are curated capability scaffolds for use by Hermes
and any future agent runtime. They define what an agent can do, when to do it,
what to expect as input, and what guardrails apply.

Skills are human-authored. They are reviewed before use. Random agent-generated
skill definitions are not allowed.

---

## Catalog

### meeting_entropy_audit

**Purpose:** Run a single meeting through the full audit pipeline.

Produces a waste score, necessity probability, classification, and async
alternative recommendation. This is the primary tool boundary for any agent
that needs to assess a meeting.

**Invocation:**

```bash
python python/hermes_meeting_tool.py meetings/weekly_alignment_sync.json
```

```python
from audit_meeting import audit_meeting_data
result = audit_meeting_data(meeting_dict)
```

See [skills/meeting_entropy_audit/SKILL.md](../skills/meeting_entropy_audit/SKILL.md).

---

### async_alternative_recommender

**Purpose:** Return the deterministic async alternative recommendation for a
scored meeting.

Takes a meeting dict and a waste score. Returns a string from the fixed
recommendation pool in `python/classify.py`. Same meeting title always
produces the same recommendation.

**Invocation:**

```python
from classify import async_recommendation
recommendation = async_recommendation(meeting_dict, waste_score)
```

See [skills/async_alternative_recommender/SKILL.md](../skills/async_alternative_recommender/SKILL.md).

---

### summary_report_writer

**Purpose:** Generate a Markdown summary report from a list of scored audit
results.

Supports three report types: batch summary, daily digest, and weekly entropy.
All generators are in `python/`.

**Invocation:**

```bash
python python/audit_all_meetings.py           # reports/summary_report.md
python python/generate_daily_digest.py        # reports/daily_digest.md
python python/generate_weekly_entropy.py      # reports/weekly_entropy.md
```

See [skills/summary_report_writer/SKILL.md](../skills/summary_report_writer/SKILL.md).

---

### cobol_output_interpreter

**Purpose:** Parse and contextualize raw two-line output from the COBOL entropy
engine. For debugging and direct binary invocation.

**Invocation:**

```bash
printf "60\n6\n0\n0\n1\n3\n" | ./cobol/entropy_engine
```

```python
from audit_meeting import ensure_cobol_binary, score_meeting
bin_path, wsl_prefix = ensure_cobol_binary()
waste_score, necessity_prob = score_meeting(meeting_dict, bin_path, wsl_prefix)
```

See [skills/cobol_output_interpreter/SKILL.md](../skills/cobol_output_interpreter/SKILL.md).

---

## Authorship Policy

Every skill in `skills/` is:

1. Written by a human
2. Reviewed against [SOUL.md](../SOUL.md) before use
3. Kept in version control alongside the code it describes

If Hermes or any other agent identifies a capability gap, the gap is documented
as a GitHub issue or PR comment. A human writes the skill. The agent does not
write its own constraints.

See [skills/README.md](../skills/README.md) for the full policy.

---

## SOUL.md Conformance

All skills must honor the Guardian's behavioral directives from
[SOUL.md](../SOUL.md):

| Directive | What it means for skills |
|---|---|
| Classify before commenting | A skill that produces prose must first produce a classification |
| Score before summarizing | No summary output without an underlying score |
| Preserve evidence | Input data must flow through to the result, not be discarded |
| Prefer brevity | Skill outputs should be precise, not reassuring |
| Entropy-reducing recommendations | Outputs must point toward cancellation, conversion, or reduction — not acceptance |
| No manufactured optimism | If the score is 94, the skill reports 94 |

A skill that violates these directives is not compliant and should not be
registered with any agent runtime until corrected.
