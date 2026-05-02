
---


# Week 11 — Tenacious-Bench v0.1

## Overview

Tenacious-Bench is a domain-specific benchmark for evaluating B2B outbound sales messaging.

It measures:

- grounding to public signals
- tone alignment
- policy violations (pricing, capacity, hallucination)
- outreach structure (clarity, CTA, single ask)

---

## External Artifacts

Dataset:  
https://huggingface.co/datasets/amaremek/tenacious-bench-v0.1  

Model:  
https://huggingface.co/amaremek/tenacious-judge-pathb  

---

## Dataset

````

tenacious_bench_v0.1/

```

- 215 tasks
- splits: train / dev / held_out
- generation modes:
  - trace-derived
  - programmatic
  - multi-LLM synthesis
  - hand-authored adversarial

---

## Training (Path B)

Preference learning setup:

```

prompt + chosen (good) + rejected (bad)

```

- chosen: Tenacious-aligned rewrite
- rejected: original candidate output

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

- ablation_results.json
- held_out_traces.jsonl

---

## Evaluation Methodology

- deterministic proxy scoring
- bootstrap confidence intervals
- paired sign-test p-values
- cost and latency instrumentation

---

## Results

- ΔA (trained vs baseline): +1.36
- ΔB (trained vs prompt): +0.74

---

## Contamination Validation

```

validation/contamination_check.py

```

Checks:

- 8-gram overlap
- embedding similarity (cosine)
- cross-partition leakage
- time-shift validation

---

## Evidence

```

evidence_graph.json

````

Links:
- dataset audit
- training data
- model artifacts
- evaluation results

---

## Reproducibility

```bash
uv run python week11/training/train_path_b_judge.py
uv run python week11/ablations/evaluate_path_b_heldout.py
````

---

## Limitations

* proxy scoring (no LLM inference pass)
* synthetic data bias
* no production integration loop

---

## Next Steps

* integrate critic into generation system
* replace proxy with LLM judge
* expand adversarial coverage
* add human evaluation layer

---

## License

See root LICENSE file


---


