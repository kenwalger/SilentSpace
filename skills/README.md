# SilentSpace Guardian — Skills

This directory contains curated skill scaffolds for Hermes and any future
agent frameworks. Skills are not generated automatically. They are written
by humans, reviewed before use, and constrained by [SOUL.md](../SOUL.md).

---

## What a Skill Is

A skill defines a bounded capability: what it does, when to call it, what
it expects, what it returns, and what it is not allowed to do. Skills are
not general-purpose reasoning prompts. They are purpose-specific boundaries.

---

## Authorship and Review Policy

**All skills in this directory are human-authored.**

Before a new skill is added:

1. A human writes the SKILL.md scaffold.
2. The scaffold is reviewed for alignment with SOUL.md — tone, scope, and guardrails.
3. The skill is added only when those two conditions are met.

Random agent-generated skill files are not allowed. An agent that generates
its own skill definition is an agent that has decided its own boundaries.
That is not how this system works.

If Hermes identifies a capability gap, the gap is documented and a human
writes the skill. Hermes may propose; humans decide.

---

## How SOUL.md Constrains Skill Behavior

[SOUL.md](../SOUL.md) is the persona and behavior contract for all Guardian
activities. Every skill in this directory must conform to its directives:

- **Classify before commenting** — produce a score or verdict before any prose
- **Score before summarizing** — no summary without underlying evidence
- **Preserve evidence** — do not discard input data when forming a conclusion
- **Prefer brevity over reassurance** — the output should be precise, not comforting
- **Recommendations must reduce organizational entropy** — not manage feelings
- **Never manufacture optimism to soften findings** — 94/100 means 94/100

Skills that produce warm, encouraging, or ambiguous output violate the contract.

---

## Current Skills

| Skill | Purpose |
|---|---|
| [meeting_entropy_audit](meeting_entropy_audit/SKILL.md) | Run a single meeting through the full audit pipeline |
| [async_alternative_recommender](async_alternative_recommender/SKILL.md) | Recommend an async alternative to a flagged meeting |
| [summary_report_writer](summary_report_writer/SKILL.md) | Generate a batch summary report from multiple audit results |
| [cobol_output_interpreter](cobol_output_interpreter/SKILL.md) | Parse and contextualize raw COBOL entropy engine output |

### Legacy

| Skill | Status |
|---|---|
| [entropy_audit](entropy_audit/SKILL.md) | Superseded by `meeting_entropy_audit` — retained for reference |

---

## Adding a New Skill

1. Create `skills/<skill_name>/SKILL.md`
2. Fill in all sections: Purpose, When to Use, Expected Inputs, Expected Outputs,
   Invocation, Guardrails, Tone Notes
3. Confirm alignment with SOUL.md
4. Submit for review before integrating with any agent runtime

Do not create a new skill directory without a complete SKILL.md.
Do not add a skill that duplicates an existing one without retiring the older version.
