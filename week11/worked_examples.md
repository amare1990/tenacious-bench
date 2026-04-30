# Worked Examples with Rubric Application

This report shows three concrete scoring paths: one programmatic, one trace-derived, and one adversarial.

---

## Example 1 — Programmatic Calibration Task

**Task ID:** TB-0001  
**Source mode:** hand_authored / programmatic calibration  
**Failure dimension:** grounded_outreach_quality

### Input

- Prospect: Maya at DataFlux
- Hiring signal: opened 7 Python engineering roles in the last 60 days after a $12M Series A
- Capacity context: 5 senior Python engineers available
- Channel: email

### Candidate Output

Subject: Request: 15 minutes on your Python hiring

The body references the 7 Python roles, Series A context, and asks for a 15-minute conversation.

### Rubric Application

| Check | Result |
|---|---|
| Body ≤ 120 words | Pass |
| Subject ≤ 60 chars | Pass |
| No banned phrases | Pass |
| No external “bench” language | Pass |
| No internal analysis leakage | Pass |
| References specific signal | Pass |
| One CTA | Pass |
| Capacity supported / no unsupported commitment | Pass |

**Score:** 8/8

---

## Example 2 — Trace-Derived Task

**Task ID:** TB-SEED-000  
**Source mode:** trace_derived  
**Failure dimension:** internal_analysis_leakage

### Input

- Prospect: Ramp
- Hiring signal: growth funding, engineering role increase, leadership change, Python/AWS/data tooling
- Capacity context: Python and ML capabilities available
- Channel: email

### Candidate Output

The Week 10 agent output includes internal-facing language such as:

- “Working angle”
- “Segment 3”
- “Public AI readiness appears to be 3/3”

### Rubric Application

| Check | Result |
|---|---|
| Body ≤ 120 words | Pass |
| Subject ≤ 60 chars | Pass |
| No banned phrases | Pass |
| No external “bench” language | Pass |
| No internal analysis leakage | Fail |
| References specific signal | Pass |
| One CTA | Pass |
| Capacity supported / no unsupported commitment | Pass |

Because internal-analysis leakage is a hard failure, the score is capped.

**Score:** 2/8

Command:

```bash
uv run python week11/scoring_evaluator.py week11/tenacious_bench_v0.1/seed_tasks/task_000.json