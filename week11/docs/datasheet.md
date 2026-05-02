
---

# Datasheet — Tenacious-Bench v0.1

## Telescopic Layer — Dataset Summary

Tenacious-Bench v0.1 is a 215-task domain-specific benchmark for evaluating B2B outbound sales outreach quality for Tenacious. It tests grounding to public signals, tone quality, pricing safety, bench-capacity honesty, CTA structure, and hallucination resistance.

Dataset split:
- Train: 111
- Dev: 68
- Held-out: 36

License: MIT License.  
License rationale: permissive reuse for research, benchmarking, and educational evaluation while preserving attribution.

---

## Periscopic Layer — Section-Level Overview

### 1. Motivation

The dataset was created because public benchmarks such as τ²-Bench retail do not measure Tenacious-specific sales behaviors: grounded hiring-signal use, bench-overcommitment avoidance, pricing-hallucination resistance, and professional B2B tone.

### 2. Composition

Each task contains an input scenario, candidate output, failure label, source mode, difficulty, and rubric metadata. Tasks cover failure modes such as missing signal reference, fabricated signal, pricing violation, bench overcommitment, banned phrases, generic template, multi-ask, and AI-maturity misroute.

### 3. Collection Process

Tasks were authored from four sources:
- trace-derived Week 10 outputs
- programmatic slot expansion
- multi-LLM synthesis
- hand-authored adversarial examples

### 4. Preprocessing, Cleaning, and Labeling

The dataset was normalized into train/dev/held_out partitions. Duplicate task IDs and duplicate candidate outputs were checked. Contamination checks include 8-gram overlap, lightweight embedding similarity, cross-partition duplicate detection, and time-shift validation hooks.

### 5. Uses

Intended uses:
- evaluating Tenacious-style sales outreach
- training Path B preference critics
- benchmarking failure-mode detection
- regression testing outreach generation systems

Not intended for:
- general-purpose NLP benchmarking
- real customer targeting
- automated production outreach without human review

### 6. Distribution

The dataset is distributed through the repository and HuggingFace:

https://huggingface.co/datasets/amaremek/tenacious-bench-v0.1

### 7. Maintenance

Future versions should add human annotation, stronger eval-tier LLM judging, expanded adversarial probes, richer time-shift provenance, and additional held-out public-signal scenarios.

---

## Microscopic Layer — Field-Level Details

Example task schema:

```json
{
  "task_id": "tb_heldout_001",
  "input": {
    "hiring_signal": "Public hiring or company-growth signal",
    "bench_summary": "Available bench/capacity context",
    "company_context": "Company segment and operational constraints",
    "public_signal_window": {
      "start": "YYYY-MM-DD",
      "end": "YYYY-MM-DD"
    }
  },
  "candidate_output": "Generated outreach message or structured message object",
  "failure_mode": "missing_signal_reference | fabricated_signal | pricing_violation | bench_overcommitment | banned_phrase | generic_template | condescending_gap | multi_ask | ai_maturity_misroute",
  "source_mode": "trace_derived | programmatic | multi_llm_synthesis | hand_adversarial",
  "difficulty": "easy | medium | hard",
  "rubric": {
    "grounding": "Checks use of public signal",
    "tone": "Checks professional Tenacious-aligned tone",
    "safety": "Checks hallucination, pricing, and capacity claims",
    "cta": "Checks clarity and single-ask structure"
  }
}
````

Field notes:

* `task_id`: stable identifier for deduplication and traceability.
* `input.hiring_signal`: public or synthetic signal used to ground the outreach.
* `input.bench_summary`: capacity context; must not be overcommitted.
* `input.public_signal_window`: supports time-shift contamination checks.
* `candidate_output`: message being evaluated.
* `failure_mode`: primary quality or policy failure being tested.
* `source_mode`: records how the task was authored.
* `rubric`: task-level scoring criteria.

---

## Limitations and Biases

Known limitations:

* The benchmark is domain-specific to Tenacious-style B2B outreach.
* Some tasks are synthetic and may reflect authoring-template bias.
* Proxy evaluation does not replace a full LLM judge or human review.
* No real customer outreach should be automated from this dataset alone.
* Time-shift provenance is implemented as a validation hook and should be deepened in v0.2.

Potential biases:

* Overrepresentation of sales-message failure modes from Week 10 traces.
* Synthetic prompts may overemphasize obvious adversarial cases.
* Tone expectations reflect Tenacious-specific standards, not universal sales norms.

---

## License

Tenacious-Bench v0.1 is released under the MIT License.

Rationale: MIT permits reuse, remixing, research benchmarking, and educational extension while preserving attribution to the original author and repository.

---

