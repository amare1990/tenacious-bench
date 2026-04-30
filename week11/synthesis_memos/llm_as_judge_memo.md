# Synthesis Memo — LLM as Judge

## Source

Common reading on LLM-based evaluation (judge models, preference learning, Prometheus-style evaluators).

---

## Core Idea

LLMs can act as evaluators (judges) by:

- scoring outputs
- ranking candidates
- detecting subtle quality differences

This enables:

> scalable evaluation beyond rule-based metrics

---

## Key Insights

### 1. Rule-based evaluation is insufficient

Rule-based systems (like current evaluator):

- catch obvious failures (length, banned phrases)
- fail on nuanced judgment:
  - tone quality
  - persuasion
  - professionalism
  - subtle grounding

Conclusion:
> rules are necessary but not sufficient

---

### 2. LLM judges require calibration

Uncalibrated LLM judges:

- are inconsistent
- hallucinate criteria
- drift across tasks

Solution:
- train or tune on preference data
- define rubric explicitly
- anchor to examples

---

### 3. Preference learning is effective

Instead of scoring directly:

- compare two outputs:
  - chosen (good)
  - rejected (bad)

Train model to prefer:

- grounded
- honest
- professional outputs

This aligns with:
> Path B: preference-tuned critic

---

### 4. Judge must reflect domain constraints

Generic LLM judges miss:

- Tenacious tone rules
- banned phrases
- “bench” restrictions
- capacity honesty

Therefore:
> domain-specific training is required

---

## Application to Tenacious-Bench

Current state:
- evaluator is rule-based

Limitations:
- misses subtle tone failures
- over-scores weak but valid outputs

Planned:

1. Generate preference pairs:
   - Week 10 output (rejected)
   - corrected Tenacious-style output (chosen)

2. Train a critic model

3. Use critic to:
   - rescore outputs
   - filter bad outputs
   - support regeneration

---

## Expected Benefits

- better detection of:
  - weak grounding
  - generic tone
  - poor CTA
- improved ranking of candidate outputs
- reduced false positives from rule-based scoring

---

## Risks

- overfitting to training pairs
- judge bias
- increased cost and latency

Mitigation:
- evaluate on held-out partition
- compare against rule-based baseline
- run ablations

---

## Conclusion

LLM-as-judge is necessary to:

> move from rule compliance → quality judgment

Tenacious-Bench will:
- keep rule-based evaluator as baseline
- add trained critic for improved evaluation (Path B)
