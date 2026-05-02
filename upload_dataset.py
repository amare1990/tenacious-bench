import json
from pathlib import Path
from datasets import Dataset, DatasetDict

ROOT = Path("week11/tenacious_bench_v0.1")


def load_split(split):
    rows = []

    for f in (ROOT / split).glob("*.json"):
        with open(f) as fh:
            task = json.load(fh)

        # Normalize into flat structure
        rows.append({
            "task_id": task.get("task_id"),
            "failure_mode": task.get("failure_mode"),
            "difficulty": task.get("difficulty"),
            "source_mode": task.get("source_mode"),

            # Keep raw input/output as JSON strings (safe)
            "input": json.dumps(task.get("input", {})),
            "candidate_output": json.dumps(task.get("candidate_output", "")),
            "rubric": json.dumps(task.get("rubric", {})),
        })

    return Dataset.from_list(rows)


dataset = DatasetDict({
    "train": load_split("train"),
    "validation": load_split("dev"),
    "test": load_split("held_out"),
})

dataset.push_to_hub("amaremek/tenacious-bench-v0.1")