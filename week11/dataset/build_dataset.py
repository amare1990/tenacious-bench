# week11/dataset/build_dataset.py

import json
import os
import sys
from collections import Counter

sys.path.append("week11")

from authoring.hand_adversarial import generate_hand_adversarial_tasks
from judge.filter_pipeline import run_judge_pipeline


def generate_trace_tasks():
    return []


def generate_programmatic_tasks():
    return []


def generate_multi_llm_tasks():
    return []


OUTPUT_PATH = "week11/outputs/dataset.jsonl"

TARGET_DISTRIBUTION = {
    "trace": 0.30,
    "programmatic": 0.30,
    "multi_llm": 0.25,
    "hand_adversarial": 0.15,
}


def build_dataset():
    all_tasks = []

    all_tasks.extend(generate_trace_tasks())
    all_tasks.extend(generate_programmatic_tasks())
    all_tasks.extend(generate_multi_llm_tasks())
    all_tasks.extend(generate_hand_adversarial_tasks())

    all_tasks = run_judge_pipeline(all_tasks)

    for task in all_tasks:
        if "source_mode" not in task:
            raise ValueError(f"Missing source_mode in task: {task.get('id')}")

    total = len(all_tasks)
    if total == 0:
        raise ValueError("No tasks generated. Wire at least one authoring mode.")

    counts = Counter(task["source_mode"] for task in all_tasks)

    print("\nDataset Composition:")
    for source_mode, count in counts.items():
        print(f"{source_mode}: {count} ({count / total:.2%})")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w") as f:
        for task in all_tasks:
            f.write(json.dumps(task) + "\n")

    print(f"\nSaved dataset to {OUTPUT_PATH}")


if __name__ == "__main__":
    build_dataset()