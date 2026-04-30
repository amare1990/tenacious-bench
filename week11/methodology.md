# Methodology — Tenacious-Bench v0.1

## 1. Path Declaration

I choose **Path B: preference-tuned judge / critic**.

### Rationale

Week 10 traces show that the Conversion Engine produces outputs that are:
- syntactically valid but weakly grounded
- often generic in tone
- prone to internal-analysis leakage
- occasionally overconfident in capacity claims

These failures are **evaluation failures**, not generation failures alone.

Therefore, the intervention is:
> train or refine a **judge/critic** that can reliably detect weak outputs and gate or re-rank them.

---

## 2. Source Artifacts

### Canonical Week 10 evaluation artifacts
- `eval/trp1-eval/trace_log.jsonl`
- `eval/trp1-eval/score_log.json`

These are used for:
- baseline comparison (Delta C)
- not for dataset construction

### Primary trace source (dataset construction)
- `data/trace_log.jsonl`

This contains:
- hiring signals
- company context
- agent-generated emails
- internal pipeline outputs

Used for:
- trace-derived task generation

### Supporting artifacts
- `probes/probe_library.md`
- `probes/failure_taxonomy.md`

Used for:
- failure dimension design
- task generation guidance

### Reference material
- Tenacious Style Guide v2

Used for:
- rubric construction
- banned phrases
- tone constraints

---

## 3. Dataset Construction

### Source Modes

- trace_derived
- hand_authored (calibration + adversarial)

Planned (final):
- programmatic variants
- multi-LLM synthesis

---

### Task Schema

Each task follows:

```json
{
  "task_id": "...",
  "source_mode": "...",
  "failure_dimension": "...",
  "input": {...},
  "candidate_output": {...},
  "rubric": {...}
}
