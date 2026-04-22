from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


SCORE_LOG_PATH = Path("eval/score_log.json")
TRACE_LOG_PATH = Path("eval/trace_log.jsonl")
BASELINE_MD_PATH = Path("baseline.md")
TAU_BENCH_ROOT = Path("external/tau2-bench")
RAW_OUTPUT_DIR = Path("eval/raw_tau_runs")
DEV_SLICE_SIZE = 30


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ci95(values: list[float]) -> tuple[float, float]:
    if len(values) <= 1:
        v = values[0] if values else 0.0
        return (round(v, 4), round(v, 4))
    m = mean(values)
    variance = sum((x - m) ** 2 for x in values) / (len(values) - 1)
    sem = math.sqrt(variance) / math.sqrt(len(values))
    margin = 1.96 * sem
    return (round(m - margin, 4), round(m + margin, 4))


def _percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    idx = max(0, min(len(sorted_values) - 1, int(math.ceil(q * len(sorted_values)) - 1)))
    return sorted_values[idx]


def _append_trace(record: dict[str, Any]) -> None:
    TRACE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TRACE_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def _write_score_log(score_log: list[dict[str, Any]]) -> None:
    SCORE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCORE_LOG_PATH.write_text(
        json.dumps(score_log, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _write_baseline_md(score_log: list[dict[str, Any]]) -> None:
    baseline = score_log[0]
    reproduction = score_log[1]

    content = f"""# Baseline

Reproduced the Week 10 retail development-slice evaluation harness and wrote task-level JSONL traces for each run.

- Dev-tier baseline mean pass@1: {baseline['mean_pass_at_1']:.2%} (95% CI {baseline['ci_95'][0]:.2%} to {baseline['ci_95'][1]:.2%})
- Reproduction check mean pass@1: {reproduction['mean_pass_at_1']:.2%} (95% CI {reproduction['ci_95'][0]:.2%} to {reproduction['ci_95'][1]:.2%})
- Cost per evaluation run: ${baseline['cost_per_run_usd']:.3f}
- p50 / p95 latency: {baseline['p50_latency_ms']} ms / {baseline['p95_latency_ms']} ms

Execution notes: this harness uses the real tau2 CLI from external/tau2-bench and preserves the required score_log.json and trace_log.jsonl output contract. If the run fails, inspect stderr from the tau2 subprocess and confirm the benchmark environment is installed with uv sync.
"""
    BASELINE_MD_PATH.write_text(content, encoding="utf-8")


def _load_json_file(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_task_records(raw: Any) -> list[dict[str, Any]]:
    """
    Normalize tau2 output into task-level records.

    Tolerates:
    - a list of task dicts
    - {"results": [...]}
    - {"tasks": [...]}
    """
    if isinstance(raw, list):
        records = raw
    elif isinstance(raw, dict):
        if isinstance(raw.get("results"), list):
            records = raw["results"]
        elif isinstance(raw.get("tasks"), list):
            records = raw["tasks"]
        else:
            raise ValueError("Could not find task list in tau2 output JSON.")
    else:
        raise ValueError("Unsupported tau2 output format.")

    normalized: list[dict[str, Any]] = []
    for idx, item in enumerate(records, start=1):
        if not isinstance(item, dict):
            continue

        task_id = str(
            item.get("task_id")
            or item.get("id")
            or item.get("name")
            or f"dev-{idx:02d}"
        )

        passed = bool(
            item.get("passed")
            if "passed" in item
            else item.get("success")
            if "success" in item
            else item.get("pass")
            if "pass" in item
            else False
        )

        latency_ms = float(
            item.get("latency_ms")
            or item.get("latency")
            or item.get("duration_ms")
            or 0
        )

        cost_usd = float(
            item.get("cost_usd")
            or item.get("cost")
            or item.get("usd_cost")
            or 0
        )

        normalized.append(
            {
                "task_id": task_id,
                "passed": passed,
                "latency_ms": latency_ms,
                "cost_usd": cost_usd,
            }
        )

    return normalized


def _latest_simulation_json(after_ts: float) -> Path:
    sim_dir = TAU_BENCH_ROOT / "data" / "simulations"
    if not sim_dir.exists():
        raise FileNotFoundError(f"Expected tau2 simulations directory at {sim_dir}")

    candidates = [
        p for p in sim_dir.rglob("*.json")
        if p.is_file() and p.stat().st_mtime >= after_ts
    ]
    if not candidates:
        raise FileNotFoundError(
            "tau2 run completed but no new simulation JSON was found in data/simulations."
        )

    return max(candidates, key=lambda p: p.stat().st_mtime)


def _run_one_trial(
    *,
    condition_name: str,
    trial_index: int,
    agent_llm: str,
    user_llm: str,
    domain: str,
    num_tasks: int,
) -> list[dict[str, Any]]:
    RAW_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    copied_output_path = RAW_OUTPUT_DIR / f"{condition_name}_trial_{trial_index:02d}.json"

    cmd = [
        "uv",
        "run",
        "tau2",
        "run",
        "--domain",
        domain,
        "--agent-llm",
        agent_llm,
        "--user-llm",
        user_llm,
        "--num-trials",
        "1",
        "--num-tasks",
        str(num_tasks),
    ]

    started_wall = time.perf_counter()
    started_fs = time.time()

    result = subprocess.run(
        cmd,
        cwd=TAU_BENCH_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    ended_wall = time.perf_counter()

    if result.returncode != 0:
        raise RuntimeError(
            "tau2-bench run failed.\n"
            f"Command: {' '.join(cmd)}\n"
            f"Return code: {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

    latest_json = _latest_simulation_json(after_ts=started_fs)
    shutil.copy2(latest_json, copied_output_path)

    raw = _load_json_file(latest_json)
    records = _extract_task_records(raw)

    wall_ms = max(0.0, (ended_wall - started_wall) * 1000.0)
    if records and all(float(r.get("latency_ms", 0)) == 0 for r in records):
        per_task = wall_ms / len(records)
        for r in records:
            r["latency_ms"] = per_task

    return records


def _run_condition(
    *,
    condition_name: str,
    trials: int,
    agent_llm: str,
    user_llm: str,
    domain: str,
    num_tasks: int,
    # temperature: float,
) -> dict[str, Any]:
    pass_rates: list[float] = []
    run_costs: list[float] = []
    run_p50s: list[float] = []
    run_p95s: list[float] = []

    for trial_index in range(1, trials + 1):
        task_records = _run_one_trial(
            condition_name=condition_name,
            trial_index=trial_index,
            agent_llm=agent_llm,
            user_llm=user_llm,
            domain=domain,
            num_tasks=num_tasks,
            # temperature=temperature,
        )

        if not task_records:
            raise ValueError(f"No task records returned for {condition_name} trial {trial_index}.")

        successes = 0
        total_cost = 0.0
        latencies: list[float] = []

        for task_index, task in enumerate(task_records, start=1):
            passed = bool(task["passed"])
            successes += int(passed)
            total_cost += float(task.get("cost_usd", 0.0))
            latency_ms = float(task.get("latency_ms", 0.0))
            latencies.append(latency_ms)

            _append_trace(
                {
                    "timestamp_utc": utc_now_iso(),
                    "benchmark": f"tau2-bench-{domain}-dev-slice",
                    "condition": condition_name,
                    "trial_index": trial_index,
                    "task_index": task_index,
                    "task_id": task["task_id"],
                    "passed": passed,
                    "latency_ms": round(latency_ms, 2),
                    "cost_usd": round(float(task.get("cost_usd", 0.0)), 6),
                }
            )

        trial_size = len(task_records)
        pass_rates.append(successes / trial_size)
        run_costs.append(total_cost)

        latencies_sorted = sorted(latencies)
        run_p50s.append(_percentile(latencies_sorted, 0.50))
        run_p95s.append(_percentile(latencies_sorted, 0.95))

    ci_low, ci_high = _ci95(pass_rates)

    return {
        "timestamp_utc": utc_now_iso(),
        "benchmark": f"tau2-bench-{domain}-dev-slice",
        "condition": condition_name,
        "trials": trials,
        "dev_slice_size": num_tasks,
        "mean_pass_at_1": round(mean(pass_rates), 4),
        "ci_95": [ci_low, ci_high],
        "cost_per_run_usd": round(mean(run_costs), 3),
        "p50_latency_ms": int(round(mean(run_p50s))),
        "p95_latency_ms": int(round(mean(run_p95s))),
        "notes": "Real tau2 CLI execution via external/tau2-bench.",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-llm", default="gpt-4.1-mini")
    parser.add_argument("--user-llm", default="gpt-4.1-mini")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--domain", default="retail")
    parser.add_argument("--num-tasks", type=int, default=DEV_SLICE_SIZE)
    parser.add_argument("--baseline-trials", type=int, default=5)
    parser.add_argument("--repro-trials", type=int, default=3)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not TAU_BENCH_ROOT.exists():
        raise FileNotFoundError(
            f"Expected tau2-bench repo at {TAU_BENCH_ROOT}. Clone it before running baseline."
        )

    if TRACE_LOG_PATH.exists():
        TRACE_LOG_PATH.unlink()

    baseline = _run_condition(
        condition_name="dev_tier_baseline",
        trials=args.baseline_trials,
        agent_llm=args.agent_llm,
        user_llm=args.user_llm,
        domain=args.domain,
        num_tasks=args.num_tasks,
        # temperature=args.temperature,
    )

    reproduction = _run_condition(
        condition_name="small_scale_reproduction_check",
        trials=args.repro_trials,
        agent_llm=args.agent_llm,
        user_llm=args.user_llm,
        domain=args.domain,
        num_tasks=args.num_tasks,
        # temperature=args.temperature,
    )

    score_log = [baseline, reproduction]
    _write_score_log(score_log)
    _write_baseline_md(score_log)

    print("Wrote eval/trace_log.jsonl")
    print("Wrote eval/score_log.json")
    print("Wrote baseline.md")


if __name__ == "__main__":
    main()
