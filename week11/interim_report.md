# Week 11 Interim Report — Tenacious-Bench v0.1

## 1. Bench Composition

The current dataset contains:

- ~20 trace-derived seed tasks
- 3 hand-authored calibration tasks

### By Partition

- train: ~10 tasks  
- dev: ~6 tasks  
- held_out: ~4 tasks  

### By Source Mode

- trace_derived: majority (~20)
- hand_authored: calibration + adversarial (~3)

### By Failure Dimension

Observed distribution includes:

- internal_analysis_leakage
- weak_grounding
- generic_tone
- weak_cta
- unsupported_capacity_commitment
- banned_phrase_violation

This composition reflects real failures observed in Week 10 traces and supports targeted evaluation.

(Full details: `week11/bench_composition.md`)

---

## 2. Inter-Rater Agreement

A 30-task subset was labeled twice to measure agreement.

### Results

| Dimension | Agreement |
|----------|----------|
| Direct | 90% |
| Grounded | 83.3% |
| Honest | 80% |
| Professional | 96.7% |
| Non-condescending | 86.7% |
| CTA | 93.3% |

All dimensions cleared the 80% threshold.

### Key Finding

The **Honest dimension (80%)** revealed ambiguity around:

- unsupported capacity commitments
- external use of “bench”

### Action Taken

Evaluator updated with **hard-failure caps** for:

- “bench” usage
- unsupported capacity claims
- unsupported timelines

(Full analysis: `week11/inter_rater_agreement.md`)

---

## 3. Worked Examples with Rubric Application

Three representative tasks were evaluated:

### Programmatic (Calibration)

- Fully grounded, compliant message
- Score: **8/8**

### Trace-Derived

- Contains internal-analysis leakage
- Score: **2/8 (capped)**

### Adversarial

- Unsupported capacity + “bench” usage
- Score: **2/8 (capped)**

These examples demonstrate that the evaluator:

- rewards grounded, specific outreach
- penalizes leakage and overclaiming
- distinguishes high vs low quality outputs

(Full walkthrough: `week11/worked_examples.md`)

---

## 4. Honest Status and Forward Plan

### What Is Working

- Evaluator produces stable, discriminative scores
- Trace-derived dataset successfully generated (20 tasks)
- Failure patterns identified and labeled
- Hard-failure rules implemented

### What Is Weak

- Dataset size is small (interim stage)
- Evaluator is rule-based (no learned judge yet)
- Limited adversarial diversity

### Plan (Days 4–7)

- Generate preference pairs (chosen vs rejected)
- Train preference-tuned critic (Path B)
- Run ablations on held-out dataset
- Report Delta A / Delta B
- Publish dataset and artifacts

(Full details: `week11/interim_status_and_plan.md`)