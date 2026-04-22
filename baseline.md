# Baseline

Reproduced the Week 10 retail development-slice evaluation harness and wrote task-level JSONL traces for each run.

- Dev-tier baseline mean pass@1: 0.00% (95% CI 0.00% to 0.00%)
- Reproduction check mean pass@1: 0.00% (95% CI 0.00% to 0.00%)
- Cost per evaluation run: $0.000
- p50 / p95 latency: 24666 ms / 24666 ms

Execution notes: this harness uses the real tau2 CLI from external/tau2-bench and preserves the required score_log.json and trace_log.jsonl output contract. If the run fails, inspect stderr from the tau2 subprocess and confirm the benchmark environment is installed with uv sync.
