

---


# Tenacious-Bench v0.1  
**TRP1 Week 10 → Week 11: Conversion Engine + Sales Evaluation Benchmark**

---

## Overview

This repository contains two integrated systems:

### Week 10 — Conversion Engine  
A full outbound sales system that:
- identifies prospects
- grounds outreach in public signals
- orchestrates email, SMS, and booking workflows
- logs structured traces for evaluation

### Week 11 — Tenacious-Bench + Learned Judge  
A domain-specific benchmark and trained critic that answers:

> *Does the system produce high-quality, production-safe sales outreach for Tenacious?*

---

## Week 11 — Key Results

| Metric | Score |
|------|------|
| Baseline mean | **6.69** |
| Prompt-only mean | **7.32** |
| Trained judge mean | **8.06** |

### Improvements

- **ΔA (trained vs baseline): +1.36**
- **95% CI:** [1.22, 1.50]

- **ΔB (trained vs prompt-only): +0.74**
- **95% CI:** [0.65, 0.82]

**Evaluation type:**  
`deterministic proxy held-out evaluation`

---

## What Was Built (Week 11)

### 1. Tenacious-Bench Dataset

- 215 tasks
- 0 duplicates after cleaning
- multi-source:
  - trace-derived
  - programmatic
  - synthesis

```

week11/tenacious_bench_v0.1/

```

---

### 2. Preference Training Data (Path B)

- 111 train pairs  
- 68 dev pairs  
- held_out excluded (no contamination)

```

week11/training_data/path_b_preference/

```

---

### 3. Trained Judge (LoRA Adapter)

- Base model: `Qwen2.5-0.5B-Instruct`
- Method: **DPO + LoRA**
- Function: preference critic for sales-quality violations

```

week11/training/outputs/path_b_judge_lora/

```

---

### 4. Held-Out Evaluation

- 36 tasks
- bootstrap confidence intervals
- cost-free deterministic scoring proxy

```

week11/ablations/

```

---

## Why Tenacious-Bench Exists

Standard benchmarks fail to capture:

- public-signal grounding
- pricing hallucination
- bench overcommitment
- tone alignment for B2B outreach

This project introduces:

> **A domain-specific benchmark + trained critic for sales reliability**

---

## Limitations

- evaluation is **proxy-based (not full LLM judge)**
- dataset partially synthetic
- trained judge not yet integrated into live generation loop

---

## Future Work (v0.2)

- eval-tier LLM judge pass
- integrate critic into generation pipeline
- expand adversarial probes
- human validation layer

---

## Repository Structure

```

week10_conversion_engine/   # outbound system
week11/
├── tenacious_bench_v0.1/
├── training_data/
├── training/
├── ablations/
└── evidence_graph.json

```

---

## Week 10 — Conversion Engine


## Author

Amare Kassa 

amaremek@gmail.com

---

## Artifacts

- Dataset: Tenacious-Bench v0.1  
- Model: Path B LoRA judge  
- Evaluation: held-out ablation results  
- Evidence: evidence_graph.json

---

