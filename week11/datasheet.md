# Tenacious-Bench v0.1 — Datasheet

## 1. Motivation

Tenacious-Bench v0.1 is a task-level benchmark designed to evaluate the quality of AI-generated outbound sales messaging for Tenacious.

The goal is to detect failures that matter in production:
- weak grounding in real hiring signals
- generic or templated tone
- internal analysis leakage into external messaging
- unsupported capacity or delivery claims
- weak or ineffective call-to-action (CTA)

This benchmark replaces reliance on τ²-Bench for this domain by focusing on **high-fidelity, domain-specific evaluation**.

---

## 2. Composition

Current dataset (interim):

- Total tasks: ~20–23
- Source modes:
  - trace_derived (from Week 10 pipeline)
  - hand_authored (calibration + adversarial examples)

- Failure dimensions:
  - internal_analysis_leakage
  - weak_grounding
  - generic_tone
  - weak_cta
  - unsupported_capacity_commitment
  - banned_phrase_violation
  - lack_of_differentiation

- Partitions:
  - train (~50%)
  - dev (~30%)
  - held_out (~20%)

---

## 3. Collection Process

Tasks were generated via:

### 1. Trace-derived generation
- Source: `data/trace_log.jsonl`
- Converted using `build_trace_seed_tasks.py`
- Extracted:
  - hiring signals
  - company context
  - generated email outputs

### 2. Hand-authored tasks
- Created to:
  - calibrate evaluator behavior
  - represent adversarial failure cases

---

## 4. Preprocessing

Each task is normalized into:

```json
{
  "task_id": "...",
  "source_mode": "...",
  "failure_dimension": "...",
  "input": {...},
  "candidate_output": {...},
  "rubric": {...}
}
