
---

# Week 11 — Tenacious-Bench v0.1

## Overview

Tenacious-Bench is a domain-specific evaluation benchmark for outbound B2B sales messaging.

It evaluates:
- grounding to public signals
- tone alignment
- policy violations (pricing, capacity, hallucination)
- outreach structure (CTA, single ask, clarity)

---

## External Artifacts

Dataset:
https://huggingface.co/datasets/amaremek/tenacious-bench-v0.1

Model:
https://huggingface.co/amaremek/tenacious-judge-pathb

---

## Dataset

```

tenacious_bench_v0.1/

```

- 215 tasks total
- train / dev / held_out split
- multi-source:
  - trace-derived
  - programmatic
  - synthesis

---

## Training (Path B)

Preference learning:

```

prompt + chosen (good) + rejected (bad)

```

- chosen: Tenacious-aligned rewrite
- rejected: original candidate_output

```

training_data/path_b_preference/

```

---

## Model

- Base: Qwen2.5-0.5B-Instruct
- Method: DPO + LoRA
- Role: **judge / critic**

```

training/outputs/path_b_judge_lora/

```

---

## Evaluation

Held-out evaluation:

```

ablations/evaluate_path_b_heldout.py

```

Outputs:

- `ablation_results.json`
- `held_out_traces.jsonl`

---

## Evaluation Type

**Deterministic proxy scoring**

This is:
- NOT model inference
- NOT LLM judge pass

Used for:
- directional improvement measurement
- cost-free evaluation

---

## Results

- ΔA: +1.36 (trained vs baseline)
- ΔB: +0.74 (trained vs prompt)

---

## Evidence

```

evidence_graph.json

```

Links:
- dataset audit
- training data
- model
- evaluation results

---

## Limitations

- proxy evaluation only
- synthetic bias
- no production deployment loop

---

## Next Steps

- integrate judge into generation pipeline
- replace proxy with LLM judge
- expand adversarial coverage


---
