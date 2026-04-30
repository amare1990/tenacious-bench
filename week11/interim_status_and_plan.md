## What Is Working

The Week 11 repo now has a functioning benchmark skeleton. The evaluator scores JSON tasks end to end and distinguishes between a strong grounded outreach example and severe policy failures.

Evidence:

- `examples/task_001.json` scores 8/8.
- `examples/task_002.json` scores 2/8.
- `examples/task_003.json` scores 2/8.
- `seed_tasks/task_000.json` scores 2/8 due to internal-analysis leakage.
- `build_trace_seed_tasks.py` generated 20 trace-derived seed tasks from `data/trace_log.jsonl`.
- The evaluator now caps scores for hard failures: unsupported capacity commitments, external use of “bench,” and internal-analysis leakage.

The project also separated the two trace sources correctly:

- `eval/trp1-eval/trace_log.jsonl` contains τ²-Bench summary results.
- `data/trace_log.jsonl` contains prospect-pipeline traces with inputs and generated emails.

## What Is Weak or Blocked

The dataset is still interim-scale, not final-scale. It has calibration examples and 20 trace-derived seed tasks, but not yet the required 200–300 tasks.

The evaluator is still mostly rule-based. It catches banned phrases, subject/body constraints, grounding overlap, CTA structure, capacity mismatch, bench-language violations, and internal-analysis leakage, but it does not yet score all five Tenacious tone markers with a calibrated LLM judge.

The current failure-dimension labels are manually assigned and need broader coverage from programmatic and multi-LLM-generated tasks.