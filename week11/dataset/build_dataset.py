# week11/dataset/build_dataset.py

import json
import os
from collections import Counter

# Import all four modes
from authoring.hand_adversarial import generate_hand_adversarial_tasks

# Placeholder imports — replace with your real ones
def generate_trace_tasks():
    return []

def generate_programmatic_tasks():
    return []

def generate_multi_llm_tasks():
    return []


OUTPUT_PATH = "week11/outputs/dataset.jsonl"

# Target distribution (documented for rubric)
TARGET_DISTRIBUTION = {
    "trace": 0.30,
    "programmatic": 0.30,
    "multi_llm": 0.25,
    "hand_adversarial": 0.15,
}


def build_dataset():
    all_tasks = []

    # Collect from each mode
    trace_tasks = generate_trace_tasks()
    prog_tasks = generate_programmatic_tasks()
    llm_tasks = generate_multi_llm_tasks()
    adv_tasks = generate_hand_adversarial_tasks()

    all_tasks.extend(trace_tasks)
    all_tasks.extend(prog_tasks)
    all_tasks.extend(llm_tasks)
    all_tasks.extend(adv_tasks)

    # Basic validation: ensure source_mode exists
    for t in all_tasks:
        if "source_mode" not in t:
            raise ValueError(f"Missing source_mode in task: {t.get('id')}")

    # Stats (useful for debugging + rubric visibility)
    counts = Counter(t["source_mode"] for t in all_tasks)
    total = len(all_tasks)

    print("\nDataset Composition:")
    for k, v in counts.items():
        print(f"{k}: {v} ({v/total:.2%})")

    # Ensure output dir exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    # Write JSONL
    with open(OUTPUT_PATH, "w") as f:
        for t in all_tasks:
            f.write(json.dumps(t) + "\n")

    print(f"\nSaved dataset to {OUTPUT_PATH}")


if __name__ == "__main__":
    build_dataset()
