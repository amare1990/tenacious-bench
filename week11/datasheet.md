

---


# Datasheet — Tenacious-Bench v0.1


## 1. Motivation

Tenacious-Bench v0.1 evaluates outbound B2B sales messaging quality for Tenacious.

It targets failures that matter in production:

- weak grounding in public hiring signals  
- generic or templated tone  
- pricing hallucination  
- bench overcommitment  
- condescending or misaligned messaging  
- multi-ask / poor CTA structure  

This replaces reliance on τ²-Bench retail with:

> **domain-specific evaluation aligned to Tenacious sales quality**

---

## 2. Dataset Composition (Final)

- Total tasks: **215**
- Train: 111  
- Dev: 68  
- Held-out: 36  

Each task contains:

```json
{
  "task_id": "...",
  "input": {...},
  "candidate_output": "...",
  "failure_mode": "...",
  "difficulty": "...",
  "rubric": {...}
}
```

---

## 3. Data Sources

### 1. Trace-derived

* extracted from Week 10 `trace_log.jsonl`
* reflects real model behavior
* used to identify authentic failure patterns

### 2. Programmatic

* template-driven generation
* ensures coverage of specific failure modes

### 3. LLM synthesis

* generated via prompt packs
* introduces adversarial and edge cases

---

## 4. Dataset Evolution (Interim → Final)

### Interim Dataset (Days 1–3)

* ~20–23 tasks
* source modes:

  * trace-derived
  * hand-authored

Failure taxonomy:

* internal_analysis_leakage
* weak_grounding
* generic_tone
* weak_cta
* unsupported_capacity_commitment
* banned_phrase_violation
* lack_of_differentiation

Purpose:

* calibrate evaluator
* define schema
* validate scoring logic

---

### Final Dataset (Days 4–7)

Expanded to:

* 215 tasks
* 3 generation modes
* normalized failure taxonomy
* strict deduplication

---

## 5. Data Cleaning

* duplicate detection and removal
* cross-partition contamination removal
* schema normalization
* failure-mode normalization

Final guarantees:

* **0 duplicate candidate outputs**
* **0 missing required fields**

---

## 6. Failure Taxonomy (Final)

* missing_signal_reference
* weak_signal_overassertion
* pricing_violation
* bench_overcommitment
* banned_phrase
* generic_template
* condescending_gap
* fabricated_signal
* multi_ask
* ai_maturity_misroute

---

## 7. Labeling Process

* trace-derived → implicit labeling from observed failures
* programmatic → explicit labeling via rules
* synthesis → labeled during prompt construction

No human annotation used.

---

## 8. Train / Dev / Held-Out Split

* held_out strictly excluded from training
* used only for evaluation
* contamination removed via deduplication

---

## 9. Evaluation Method

Evaluation uses:

```text
deterministic proxy held-out evaluation
```

This method:

* scores outputs via rule-based evaluator
* estimates improvement directionally
* does NOT perform model inference

---

## 10. Limitations

* proxy evaluation (not full LLM judge)
* partially synthetic dataset
* no human annotation
* domain-specific bias

---

## 11. Ethical Considerations

* no real user data
* all prospects synthetic
* avoids sensitive information

---

## 12. Intended Use

Intended for:

* training sales-quality critics (Path B)
* evaluating outbound messaging systems
* enforcing grounding and tone

Not intended for:

* general NLP benchmarks
* open-domain generation

---

## 13. Future Improvements (v0.2)

* eval-tier LLM judge evaluation
* human annotation layer
* increased trace-derived proportion
* adversarial expansion


---






