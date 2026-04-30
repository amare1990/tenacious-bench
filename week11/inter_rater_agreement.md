# Inter-Rater Agreement

## Method

I hand-labeled a 30-task subset, then relabeled the same tasks after a delay without viewing the first labels.

The agreement threshold for each rubric dimension is 80%. Any dimension below 80% triggers rubric revision.

## Agreement Matrix

| Rubric Dimension | First/Second Agreement | Status | Action |
|---|---:|---|---|
| Direct | 27/30 = 90% | Pass | No revision |
| Grounded | 25/30 = 83.3% | Pass | Clarified specific-signal examples |
| Honest | 24/30 = 80% | Pass | Added hard-failure rule for unsupported capacity |
| Professional | 29/30 = 96.7% | Pass | No revision |
| Non-condescending | 26/30 = 86.7% | Pass | Added examples of gap-framing failures |
| CTA / One Ask | 28/30 = 93.3% | Pass | No revision |

## Interpretation

All dimensions cleared the 80% threshold. The weakest dimension was Honest because unsupported capacity commitments were initially ambiguous. I revised the evaluator to cap scores for disqualifying capacity and external-bench-language failures.

## Revision Notes

The scoring evaluator now treats these as hard failures:

- use of “bench” in prospect-facing copy
- unsupported capacity commitment
- unsupported price or delivery timeline claim
