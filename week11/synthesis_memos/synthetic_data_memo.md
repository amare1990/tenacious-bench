# Synthesis Memo — Synthetic Data for Evaluation Benchmarks

## Source

Common reading on synthetic data generation for benchmarks and training.

---

## Core Idea

Synthetic data is used to:

- expand dataset coverage beyond real logs
- generate edge cases not present in traces
- create controlled variations of failure modes

However, synthetic data introduces risks:

- distribution mismatch
- pattern leakage
- overfitting to generation style

---

## Key Insights

### 1. Synthetic data should be anchored in real traces

Purely synthetic tasks tend to:
- lack realism
- fail to capture real-world noise

Best practice:
> Use real traces as seeds, then generate controlled variations

This aligns with Tenacious-Bench design:
- trace-derived tasks → base
- synthetic tasks → expansion

---

### 2. Diversity matters more than volume

Adding 100 similar synthetic tasks is worse than:
- 20 diverse adversarial tasks

Important dimensions to vary:
- company size
- hiring signal strength
- AI maturity
- urgency
- contradiction scenarios

---

### 3. Adversarial generation is high value

Synthetic data is especially useful for:

- hallucination traps
- overcommitment scenarios
- ambiguous signals
- conflicting constraints

These are rare in logs but critical for evaluation.

---

## Application to Tenacious-Bench

Current state:
- dataset is mostly trace-derived (~20 tasks)

Planned:
- add synthetic tasks via:
  - programmatic variation
  - LLM-generated adversarial cases

Example:

Base trace:
> “Opened 3 backend roles”

Synthetic variants:
- “Opened 3 roles but hiring paused”
- “Claims hiring but no public signal”
- “Needs 10 engineers, bench has 2”

---

## Risks

- synthetic tasks may reflect model bias
- evaluator may overfit to synthetic phrasing
- duplication of patterns

Mitigation:
- mix with trace-derived tasks
- use contamination checks
- manually review adversarial examples

---

## Conclusion

Synthetic data is necessary for:

- coverage
- adversarial testing
- robustness

But must be:
> grounded in real traces and carefully diversified

Tenacious-Bench will use synthetic data primarily for:
- adversarial slices
- programmatic variants
