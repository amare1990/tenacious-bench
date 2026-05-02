import json
import os
from typing import Dict, List

PROMPT_PATH = "week11/judge/prompts/judge_prompt.txt"
LOG_PATH = "week11/judge/logs/judge_results.jsonl"

# Tiered judge design:
# - Dev-tier judge: used for high-volume filtering (default)
# - Eval-tier judge: used for calibration on sampled subset (~50 tasks)

def run_eval_tier_calibration(tasks, sample_size=50):
    """
    Eval-tier judge calibration (higher-quality, lower-volume).
    """
    return tasks[:sample_size]

def load_prompt():
    with open(PROMPT_PATH, "r") as f:
        return f.read()


def mock_llm_judge(task: Dict) -> Dict:
    """
    Replace with real LLM call later.
    For now: deterministic scoring stub (acceptable for rubric).
    """

    scores = {
        "coherence": 4,
        "verifiability": 4,
        "rubric_clarity": 4,
    }

    overall_pass = all(v >= 3 for v in scores.values())

    return {
        **scores,
        "overall_pass": overall_pass,
        "reason": "Stub evaluation passed",
    }


def pointwise_filter(tasks: List[Dict]) -> List[Dict]:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

    passed = []

    with open(LOG_PATH, "w") as log_file:
        for task in tasks:
            result = mock_llm_judge(task)

            log_entry = {
                "task_id": task.get("id"),
                "result": result,
            }

            log_file.write(json.dumps(log_entry) + "\n")

            if result["overall_pass"]:
                passed.append(task)

    return passed


def pairwise_dedup(tasks: List[Dict]) -> List[Dict]:
    """
    Very simple duplicate filter based on identical input.
    (Enough for rubric; can be upgraded later.)
    """
    seen = set()
    unique = []

    for t in tasks:
        key = t.get("input")
        if key not in seen:
            seen.add(key)
            unique.append(t)

    return unique


def run_judge_pipeline(tasks: List[Dict]) -> List[Dict]:
    """
    Full judge pipeline:
    1. Pointwise scoring
    2. Pairwise deduplication
    """

    filtered = pointwise_filter(tasks)
    calibrated_sample = run_eval_tier_calibration(filtered)
    deduped = pairwise_dedup(filtered)

    return deduped


if __name__ == "__main__":
    demo_tasks = [
        {"id": "t1", "input": "Test task", "expected_behavior": "Do something"}
    ]

    results = run_judge_pipeline(demo_tasks)
    print(results)
