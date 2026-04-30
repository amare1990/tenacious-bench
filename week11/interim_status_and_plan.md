# Interim Status and Forward Plan

## What Is Working

The Week 11 repo now has a functioning benchmark skeleton. The evaluator scores JSON tasks end to end and distinguishes between a strong grounded outreach example and severe policy failures.

Evidence:

- `task_001.json` scores 7/7.
- `task_002.json` scores 2/7.
- `task_003.json` scores 2/7.
- The evaluator now caps scores for hard failures such as unsupported capacity commitments and external use of “bench.”

The project also found the correct trace source:

- `eval/trp1-eval/trace_log.jsonl` contains τ²-Bench summary results.
- `data/trace_log.jsonl` contains prospect-pipeline traces with inputs and generated emails.

## What Is Weak or Blocked

The trace-derived conversion is still early. Some traces are incomplete or missing email output fields, so the conversion script needs robust fallback handling and skip accounting.

The evaluator is still mostly rule-based. It can detect banned phrases, subject/body constraints, grounding overlap, capacity mismatch, and bench-language violations, but it does not yet score all five Tenacious tone markers with a calibrated LLM judge.

The dataset is not yet at 200–300 tasks. The current state is calibration + seed extraction, not final benchmark scale.

## Day 4 Plan

I will proceed with Path B: preference-tuned judge / critic.

Day 4 work:

1. Complete path-specific reading synthesis for DPO, SimPO/ORPO, and Prometheus-style judge training.
2. Convert benchmark tasks into preference pairs:
   - rejected = Week 10 weak output
   - chosen = corrected Tenacious-style output
3. Add metadata for failure dimension, source mode, and split.
4. Run contamination checks before final partitioning.

## Days 5–6 Plan

1. Train a small judge / critic model or lightweight preference scorer.
2. Compare:
   - Week 10 baseline
   - Week 10 system + trained critic
   - prompt-only critic baseline
3. Run paired scoring on held-out tasks.
4. Report Delta A, Delta B, cost per task, and latency.
5. Produce `ablation_results.json` and `held_out_traces.jsonl`.

## Day 7 Plan

1. Publish HuggingFace dataset.
2. Publish model card if a trained critic artifact is produced.
3. Write the technical blog post.
4. Produce CEO/CFO memo.
5. Add evidence graph mapping numeric claims to source files.
