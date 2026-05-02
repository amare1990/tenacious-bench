

---

# Tenacious-Bench v0.1  
**TRP1 Week 10 → Week 11: Conversion Engine + Sales Evaluation Benchmark**

---

## Overview

This repository contains two integrated systems:

### Week 10 — Conversion Engine
A production-style outbound sales system that:
- identifies prospects
- grounds outreach in public signals
- generates structured messages (email/SMS)
- logs execution traces for evaluation

### Week 11 — Tenacious-Bench + Learned Judge
A domain-specific evaluation benchmark and trained critic answering:

> *Does the system produce high-quality, production-safe B2B outreach?*

---

## 🔗 Artifacts

- Dataset: https://huggingface.co/datasets/amaremek/tenacious-bench-v0.1  
- Model (Path B Judge): https://huggingface.co/amaremek/tenacious-judge-pathb  

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
Deterministic proxy held-out evaluation (see limitations)

---

## What Was Built (Week 11)

### 1. Tenacious-Bench Dataset
- 215 tasks (train/dev/held_out)
- multi-source:
  - trace-derived
  - programmatic
  - multi-LLM synthesis
  - hand-authored adversarial

### 2. Preference Training Data (Path B)
- 111 train pairs
- 68 dev pairs
- held_out excluded (no contamination)

### 3. Trained Judge (LoRA)
- Base: Qwen2.5-0.5B-Instruct
- Method: DPO + LoRA
- Role: preference critic

### 4. Held-Out Evaluation
- bootstrap CI + p-values
- cost/timing instrumentation
- ablation harness

---

## Why Tenacious-Bench Exists

Standard benchmarks miss:

- public-signal grounding
- pricing hallucination
- bench overcommitment
- tone alignment for B2B outreach

This project introduces:

> **A domain-specific benchmark + learned critic for sales reliability**

---

## Setup & Reproduction

### Install

```bash
git clone <repo-url>
cd conversion-engine
uv pip install -r requirements.txt
````

### Build Dataset

```bash
uv run python week11/dataset/build_dataset.py
```

### Run Contamination Checks

```bash
uv run python week11/validation/contamination_check.py
```

### Train Path B Judge

```bash
uv run python week11/training/train_path_b_judge.py
```

### Run Evaluation

```bash
uv run python week11/ablations/evaluate_path_b_heldout.py
```

---

## Repository Structure

```
week10_conversion_engine/
week11/
├── tenacious_bench_v0.1/
├── dataset/
├── training_data/
├── training/
├── ablations/
├── validation/
├── judge/
└── docs/
```

---

## Limitations

* proxy evaluation (not full LLM judge inference)
* partial synthetic dataset
* trained critic not yet integrated into generation loop

---

## Future Work

* eval-tier LLM judge pass
* integrate critic into generation pipeline
* expand adversarial dataset coverage
* human evaluation layer

---

## License

MIT License (see LICENSE file)

---

## Author

Amare Kassa

[amaremek@gmail.com](mailto:amaremek@gmail.com)



---

