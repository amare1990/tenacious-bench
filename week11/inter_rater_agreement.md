# Inter-Rater Agreement

## 1. Method

A 30-task subset was sampled from the dataset across:

- multiple partitions (seed + examples)
- multiple failure dimensions
- both trace-derived and hand-authored tasks

Each task was labeled twice by the same annotator with a delay between passes, without access to the first labels.

Agreement is computed per rubric dimension.

Threshold:
> Any dimension below **80% agreement triggers rubric revision**

---

## 2. Agreement Matrix

| Rubric Dimension | Agreement | Status | Action |
|---|---:|---|---|
| Direct | 27/30 = 90% | Pass | No revision |
| Grounded | 25/30 = 83.3% | Pass | Clarified specific-signal examples |
| Honest | 24/30 = 80% | Borderline | Added hard-failure rules for unsupported capacity |
| Professional | 29/30 = 96.7% | Pass | No revision |
| Non-condescending | 26/30 = 86.7% | Pass | Added examples of gap-framing failures |
| CTA / One Ask | 28/30 = 93.3% | Pass | No revision |

---

## 3. Interpretation

All rubric dimensions met or exceeded the 80% threshold.

The weakest dimension was **Honest (80%)**, indicating ambiguity in how unsupported claims (capacity, timelines) should be judged.

This surfaced a key issue:
> The evaluator initially treated overcommitment as a soft failure rather than a disqualifying error.

---

## 4. Revision Loop (Critical)

### Before revision

- Unsupported capacity commitments were inconsistently penalized
- “Bench” usage was sometimes ignored if other signals passed
- Result: over-permissive scoring

### After revision

The evaluator was updated to include **hard-failure caps**:

- external use of “bench” → disqualifying
- unsupported capacity commitment → disqualifying
- unsupported delivery/timeline claims → disqualifying

Implementation:

```text
score = min(score, 2) if hard_failure_detected