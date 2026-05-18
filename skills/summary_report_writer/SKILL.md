# Skill: summary_report_writer

**Status:** Human-authored scaffold
**Constraint:** SOUL.md — score before summarizing, preserve evidence

---

## Purpose

Given a list of scored meeting audit results, generate one of the following
summary reports:

- **Batch summary** (`reports/summary_report.md`) — full organizational entropy
  snapshot across all audited meetings
- **Daily digest** (`reports/daily_digest.md`) — end-of-day regret audit
  focusing on async candidates and top offenders
- **Weekly entropy** (`reports/weekly_entropy.md`) — recurring meeting waste
  patterns and weekly person-hours lost

This skill does not score meetings. It accepts pre-scored results and assembles
the report. Scoring happens in `meeting_entropy_audit`.

---

## When to Use

- After running `meeting_entropy_audit` on a batch of meetings
- When a scheduled audit workflow needs to produce a human-readable output
- When Hermes needs to summarize a set of results into a structured document

Do not use this skill on raw meeting JSON. Score first. Summarize after.

---

## Expected Inputs

A list of audit result dicts, each from `audit_meeting_data()`:

```python
[
    {
        "title": "string",
        "waste_score": 92,
        "necessity_prob": 8,
        "classification": "Corporate Heat Death Event: Entropy Made Flesh — ...",
        "recommendation": "Cancel and initiate a post-mortem...",
        "meeting": { ... }
    },
    ...
]
```

---

## Expected Outputs

A Markdown report string written to one of:

- `reports/summary_report.md` — via `python/audit_all_meetings.py`
- `reports/daily_digest.md` — via `python/generate_daily_digest.py`
- `reports/weekly_entropy.md` — via `python/generate_weekly_entropy.py`

---

## Invocation

**Batch summary:**

```bash
python python/audit_all_meetings.py
```

**Daily digest:**

```bash
python python/generate_daily_digest.py
# or via the scheduled script:
bash scripts/run_daily_regret_audit.sh
```

**Weekly entropy:**

```bash
python python/generate_weekly_entropy.py
# or via the scheduled script:
bash scripts/run_weekly_entropy_summary.sh
```

**Python (direct, for custom pipelines):**

```python
import sys
sys.path.insert(0, "python")
from audit_all_meetings import generate_summary
from generate_daily_digest import generate_daily_digest
from generate_weekly_entropy import generate_weekly_entropy

# results = list of audit_meeting_data() return values
summary_md = generate_summary(results)
digest_md = generate_daily_digest(results)
weekly_md = generate_weekly_entropy(results)
```

---

## Guardrails

- Do not generate summaries from partial result sets without clearly labeling them as partial.
- Do not modify waste scores or classification labels in the summary output.
- Do not add LLM-generated narrative to summary sections. The copy is fixed by the generator functions.
- Reports are written to `reports/`. Do not write them elsewhere without updating the relevant generator.
- This skill has no network access and does not post reports anywhere.

---

## Tone Notes (SOUL.md)

Summary reports are audit filings, not engagement documents. They do not
celebrate good meetings or soften bad ones. The data leads. The prose describes
it accurately. Aggregate statistics are stated without commentary on whether
the numbers are "surprising" or "concerning." They are what they are.

See [SOUL.md](../../SOUL.md) for the full behavioral contract.
