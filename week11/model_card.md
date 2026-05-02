

---


# Model Card — Path B Judge (LoRA Adapter)

## 1. Overview

This model is a **preference-trained judge / critic** for evaluating outbound sales messaging quality in the Tenacious domain.

It is trained to distinguish between:
- compliant (high-quality) outreach
- failure-mode outputs (unsafe or low-quality)

---

## 2. Model Details

- Base model: `Qwen/Qwen2.5-0.5B-Instruct`
- Training method: **DPO (Direct Preference Optimization)**
- Fine-tuning: **LoRA adapter**
- Output type: preference critic (not generator)

---

## 3. Training Data

Path B preference dataset:

- 111 train pairs
- 68 dev pairs
- format: (prompt, chosen, rejected)

Source:

```

week11/training_data/path_b_preference/

```

---

## 4. Training Procedure

- LoRA applied to attention and MLP layers
- DPO objective used for preference alignment
- training performed on Colab GPU (T4)

Script:

```

week11/training/train_path_b_judge.py

````

---

## 5. Intended Use

This model is intended to:

- evaluate candidate outreach messages
- detect policy violations
- act as a critic in a generation loop

Example use cases:

- filtering generated emails
- scoring outbound quality
- enforcing Tenacious style constraints

---

## 6. Evaluation

Evaluation was performed using:

```text
deterministic proxy held-out evaluation
````

Results:

* Baseline: 6.69
* Prompt-only: 7.32
* Trained judge: 8.06

Improvements:

* ΔA: +1.36 (vs baseline)
* ΔB: +0.74 (vs prompt-only)

---

## 7. Limitations

* proxy evaluation only (no model inference loop)
* small dataset (215 tasks)
* synthetic bias in training data
* not deployed in real production pipeline

---

## 8. Risks

Potential failure modes:

* false positives (over-rejection)
* missed subtle violations
* overfitting to synthetic patterns

---

## 9. Ethical Considerations

* no real customer data used
* model enforces safer, more honest communication
* avoids hallucinated claims and misleading pricing

---

## 10. Future Work

* integrate into generation loop
* replace proxy evaluation with LLM judge
* scale dataset and training
* introduce human evaluation

---

## 11. Artifacts

Model location:

```
week11/training/outputs/path_b_judge_lora/
```

Adapter files:

* adapter_model.safetensors
* adapter_config.json


---
