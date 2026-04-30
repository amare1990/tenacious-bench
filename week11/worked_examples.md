# Worked Examples with Rubric Application

This report shows three concrete scoring paths: one programmatic, one trace-derived, and one adversarial.

---

## Example 1 — Programmatic Task

**Task ID:** TB-0001  
**Source mode:** hand_authored / programmatic calibration  
**Failure dimension:** grounded_outreach_quality

### Input

- Prospect: Maya at DataFlux
- Hiring signal: opened 7 Python engineering roles in the last 60 days after a $12M Series A
- Bench summary: 5 senior Python engineers available
- Channel: email

### Candidate Output

Subject: Request: 15 minutes on your Python hiring

Body references the 7 Python roles, Series A context, and asks for a 15-minute conversation.

### Rubric Application

| Check | Result |
|---|---|
| Body ≤ 120 words | Pass |
| Subject ≤ 60 chars | Pass |
| No banned phrases | Pass |
| No external “bench” language | Pass |
| References specific signal | Pass |
| One CTA | Pass |
| Capacity supported / no unsupported commitment | Pass |

**Score:** 7/7

---

## Example 2 — Trace-Derived Task

**Task ID:** TB-SEED-000  
**Source mode:** trace_derived  
**Failure dimension:** weak_grounding_or_generic_tone

### Input

The task was converted from `data/trace_log.jsonl`. It includes the prospect profile, hiring-signal summary, AI maturity profile, competitor-gap brief, bench-match summary, policy result, and generated email.

### Candidate Output

The candidate output is the original Week 10 agent email from the trace.

### Rubric Application

| Check | Result |
|---|---|
| Body length | Evaluated by script |
| Subject length | Evaluated by script |
| Banned phrase scan | Evaluated by script |
| External “bench” language | Evaluated by script |
| Signal reference | Evaluated by script |
| CTA count | Evaluated by script |
| Capacity support | Evaluated by script |

**Score:** Run with:

```bash
uv run python week11/scoring_evaluator.py week11/tenacious_bench_v0.1/seed_tasks/task_000.json
