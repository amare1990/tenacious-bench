from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


SCORE_LOG_PATH = Path("eval/score_log.json")
TRACE_LOG_PATH = Path("eval/trace_log.jsonl")
BASELINE_MD_PATH = Path("baseline.md")


def append_trace(record: dict) -> None:
    TRACE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TRACE_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_score_log(score_log: list[dict]) -> None:
    SCORE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SCORE_LOG_PATH.open("w", encoding="utf-8") as f:
        json.dump(score_log, f, indent=2, ensure_ascii=False)


def write_baseline_md() -> None:
    content = """# Baseline

Reproduced the initial Week 10 baseline harness scaffold and logging path.
Current baseline is a local placeholder pending full tau2-bench integration.

- Evaluation slice: local placeholder
- Trace logging: enabled
- Score logging: enabled
- Cost per run: not yet measured
- Confidence interval: not yet measured

Next step: connect the tau2-bench retail baseline and log reproducible runs.
"""
    BASELINE_MD_PATH.write_text(content, encoding="utf-8")


def main() -> None:
    run_record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "benchmark": "tau2-bench-retail-placeholder",
        "status": "scaffolded",
        "pass_at_1": None,
        "ci_95": None,
        "cost_per_run": None,
        "latency_ms": None,
        "notes": "Placeholder until tau2-bench harness is wired.",
    }

    append_trace(run_record)
    write_score_log([run_record])
    write_baseline_md()

    print("Wrote eval/trace_log.jsonl")
    print("Wrote eval/score_log.json")
    print("Wrote baseline.md")


if __name__ == "__main__":
    main()
