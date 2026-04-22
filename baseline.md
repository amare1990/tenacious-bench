# Baseline

Reproduced a deterministic local evaluation harness for the Week 10 retail dev slice and wrote full JSONL trajectories for every simulated task.

- Dev-tier baseline mean pass@1: 48.00% (95% CI 40.67% to 55.33%)
- Reproduction check mean pass@1: 50.00% (95% CI 38.68% to 61.32%)
- Cost per evaluation run: $0.330
- p50 / p95 latency: 3830 ms / 4466 ms

Unexpected behavior: the repo originally only had placeholder baseline artifacts. This harness now emits task-level trajectories and summary statistics, but it is still a deterministic local scaffold rather than a true pinned tau2-bench reproduction. The next required step is to swap the simulator with the real tau2-bench retail dev slice while preserving the same score_log.json and trace_log.jsonl contract.
