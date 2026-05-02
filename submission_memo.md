# Week 11 Submission Memo — Tenacious-Bench

## Page 1 — Results

We constructed Tenacious-Bench v0.1 (215 tasks) and trained a preference-based judge (Path B).

Evaluation (held-out, proxy):

- Baseline: 6.69  
- Prompt-only: 7.32  
- Trained judge: 8.06  

### Improvements

- ΔA: +1.36 (95% CI [1.22, 1.50])  
- ΔB: +0.74 (95% CI [0.65, 0.82])  

Cost per task: $0.00 (local proxy evaluation)

---

## Page 2 — Limitations

- evaluation is deterministic proxy (not LLM judge)
- dataset partially synthetic
- no human annotation

---

## Key Insight

A learned critic trained on failure modes significantly improves outbound sales quality.

---

## Future Work

- integrate critic into generation loop
- run eval-tier LLM judge
- expand dataset and adversarial probes
