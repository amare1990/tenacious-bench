# Building Tenacious-Bench: A Domain-Specific Evaluation for Sales AI

## Motivation

In Week 10, I built a Conversion Engine for Tenacious: a system that identifies prospects, grounds outreach in public signals, and orchestrates email → SMS → booking workflows.

But a critical question remained:

> How do we know the generated outreach is actually good?

Standard benchmarks like τ²-Bench retail do not capture:
- grounding to public signals
- pricing hallucination
- bench overcommitment
- tone alignment in B2B outreach

So in Week 11, I built **Tenacious-Bench**.

---

## What is Tenacious-Bench?

Tenacious-Bench v0.1 is a domain-specific benchmark for evaluating outbound sales messaging.

It contains:
- 215 tasks
- train/dev/held_out split
- structured failure modes (pricing, tone, grounding, etc.)

Key design goals:
- detect production-critical failures
- enforce grounded, honest communication
- evaluate style, not just correctness

---

## Dataset Construction

The dataset was built from:

### 1. Trace-derived data
- extracted from Week 10 `trace_log.jsonl`
- captures real model failures

### 2. Programmatic generation
- systematic coverage of failure modes

### 3. LLM synthesis
- adversarial and edge-case generation

After cleaning:
- 0 duplicates
- 0 missing fields
- strict held-out separation

---

## Training a Judge (Path B)

Instead of improving generation directly, I trained a **critic model**.

### Approach:
- preference learning (DPO)
- LoRA adapter
- base model: Qwen2.5-0.5B-Instruct

Training data:
- 111 train pairs
- 68 dev pairs
- chosen vs rejected outputs

The model learns:
> what *not* to say in outbound sales

---

## Evaluation

Evaluation was performed on a held-out set of 36 tasks using:

> deterministic proxy scoring

Results:

| Metric | Score |
|------|------|
| Baseline | 6.69 |
| Prompt-only | 7.32 |
| Trained judge | 8.06 |

### Improvements

- ΔA: +1.36 (vs baseline)  
- ΔB: +0.74 (vs prompt-only)  
- 95% CI confirms statistical significance  

---

## Key Insight

Improving sales AI is not just about better prompts.

It requires:
- domain-specific benchmarks
- failure-mode-aware training
- learned critics, not just generators

---

## Limitations

- proxy evaluation (not full LLM judge)
- synthetic data bias
- no live deployment loop

---

## Future Work

- integrate judge into generation pipeline
- use LLM judge for evaluation
- expand adversarial coverage
- human-in-the-loop validation

---

## Conclusion

Tenacious-Bench demonstrates that:

> Domain-specific evaluation + learned critics can significantly improve AI system reliability.

---

## Links

- GitHub repo: https://github.com/amare1990/tenacious-bench
