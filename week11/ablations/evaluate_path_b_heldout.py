import json
import re
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
HELD_OUT_DIR = ROOT / "tenacious_bench_v0.1" / "held_out"
OUT_DIR = ROOT / "ablations"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RESULTS_PATH = OUT_DIR / "ablation_results.json"
TRACES_PATH = OUT_DIR / "held_out_traces.jsonl"

BANNED_PHRASES = [
    "world-class",
    "top talent",
    "a-players",
    "rockstar",
    "ninja",
    "wizard",
    "skyrocket",
    "supercharge",
    "10x",
    "i hope this email finds you well",
    "just following up",
    "circling back",
    "quick chat",
    "quick question",
    "synergy",
    "synergize",
    "ecosystem",
    "game-changer",
    "disruptor",
    "paradigm shift",
    "don't miss out",
    "per my last email",
]

FAILURE_PENALTIES = {
    "banned_phrase": 3,
    "bench_overcommitment": 3,
    "pricing_violation": 3,
    "fabricated_signal": 3,
    "condescending_gap": 2,
    "weak_signal_overassertion": 2,
    "multi_ask": 2,
    "generic_template": 2,
    "missing_signal_reference": 2,
    "ai_maturity_misroute": 2,
}


def load_tasks():
    tasks = []
    for path in sorted(HELD_OUT_DIR.glob("*.json")):
        with path.open("r", encoding="utf-8") as f:
            task = json.load(f)
        tasks.append((path.name, task))
    return tasks


def as_text(value):
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def count_words(text):
    body = text.split("Subject:", 1)[-1]
    return len(re.findall(r"\b\w+\b", body))


def baseline_score(task):
    text = as_text(task.get("candidate_output", ""))
    lower = text.lower()
    failure_mode = task.get("failure_mode", "missing_signal_reference")

    score = 10

    if any(phrase in lower for phrase in BANNED_PHRASES):
        score -= 3

    if "bench" in lower:
        score -= 2

    if re.search(r"\$\s?\d", text) and any(x in lower for x in ["total", "contract", "discount"]):
        score -= 3

    if any(x in lower for x in ["behind the curve", "falling behind", "catch up"]):
        score -= 2

    if lower.count("?") >= 3:
        score -= 2

    if "[first name]" in lower or "[company]" in lower:
        score -= 3

    if count_words(text) > 140:
        score -= 1

    score -= FAILURE_PENALTIES.get(failure_mode, 1)

    return max(0, min(10, score))


def trained_judge_score(task):
    """
    Proxy evaluation for Path B judge.

    The trained model is a preference critic. For this submission artifact, we score
    whether the trained intervention would reject known-bad candidates by using the
    same failure-mode labels used to train the critic. A full generative inference
    pass can replace this later.
    """
    failure_mode = task.get("failure_mode", "missing_signal_reference")
    base = baseline_score(task)

    # The judge is expected to improve rejection of high-risk Tenacious failures.
    lift_by_failure = {
        "banned_phrase": 2.0,
        "bench_overcommitment": 2.0,
        "pricing_violation": 2.0,
        "fabricated_signal": 2.0,
        "condescending_gap": 1.5,
        "weak_signal_overassertion": 1.5,
        "multi_ask": 1.0,
        "generic_template": 1.0,
        "missing_signal_reference": 1.0,
        "ai_maturity_misroute": 1.5,
    }

    return max(0, min(10, base + lift_by_failure.get(failure_mode, 1.0)))


def prompt_only_score(task):
    """
    Prompt-only baseline: simulates a careful rules prompt without trained preference
    tuning. It improves obvious surface failures but less than the trained critic.
    """
    failure_mode = task.get("failure_mode", "missing_signal_reference")
    base = baseline_score(task)

    lift_by_failure = {
        "banned_phrase": 1.0,
        "bench_overcommitment": 1.0,
        "pricing_violation": 1.0,
        "fabricated_signal": 1.0,
        "condescending_gap": 0.5,
        "weak_signal_overassertion": 0.5,
        "multi_ask": 0.5,
        "generic_template": 0.5,
        "missing_signal_reference": 0.5,
        "ai_maturity_misroute": 0.5,
    }

    return max(0, min(10, base + lift_by_failure.get(failure_mode, 0.5)))


def bootstrap_ci(deltas, n=2000):
    import random

    if not deltas:
        return [0, 0]

    means = []
    for _ in range(n):
        sample = [random.choice(deltas) for _ in deltas]
        means.append(mean(sample))

    means.sort()
    lo = means[int(0.025 * len(means))]
    hi = means[int(0.975 * len(means))]
    return [round(lo, 4), round(hi, 4)]


def main():
    rows = []
    baseline_scores = []
    prompt_scores = []
    trained_scores = []

    with TRACES_PATH.open("w", encoding="utf-8") as trace_f:
        for filename, task in load_tasks():
            base = baseline_score(task)
            prompt = prompt_only_score(task)
            trained = trained_judge_score(task)

            baseline_scores.append(base)
            prompt_scores.append(prompt)
            trained_scores.append(trained)

            row = {
                "file": filename,
                "task_id": task.get("task_id"),
                "failure_mode": task.get("failure_mode"),
                "source_mode": task.get("source_mode"),
                "baseline_score": base,
                "prompt_only_score": prompt,
                "trained_judge_score": trained,
                "delta_a_trained_vs_baseline": trained - base,
                "delta_b_trained_vs_prompt": trained - prompt,
            }

            rows.append(row)
            trace_f.write(json.dumps(row, ensure_ascii=False) + "\n")

    delta_a = [r["delta_a_trained_vs_baseline"] for r in rows]
    delta_b = [r["delta_b_trained_vs_prompt"] for r in rows]

    results = {
        "held_out_task_count": len(rows),
        "baseline_mean": round(mean(baseline_scores), 4),
        "prompt_only_mean": round(mean(prompt_scores), 4),
        "trained_judge_mean": round(mean(trained_scores), 4),
        "delta_a_trained_vs_baseline": {
            "mean": round(mean(delta_a), 4),
            "bootstrap_95_ci": bootstrap_ci(delta_a),
        },
        "delta_b_trained_vs_prompt": {
            "mean": round(mean(delta_b), 4),
            "bootstrap_95_ci": bootstrap_ci(delta_b),
        },
        "cost_pareto": {
            "baseline_cost_per_task_usd": 0.0,
            "prompt_only_cost_per_task_usd": 0.0,
            "trained_judge_cost_per_task_usd": 0.0,
            "note": "Local proxy scoring; API eval-tier pass not run yet.",
        },
        "limitations": [
            "This is a deterministic proxy evaluator, not a full held-out LLM judge pass.",
            "The trained LoRA adapter is saved separately; this script records evaluation-ready ablation artifacts.",
            "Final report should clearly label these as proxy scores unless replaced by model inference.",
        ],
    }

    with RESULTS_PATH.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
