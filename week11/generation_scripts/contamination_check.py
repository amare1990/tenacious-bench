import json
from collections import Counter
from itertools import combinations
from pathlib import Path

DATASET_DIR = Path("week11/tenacious_bench_v0.1")
OUTPUT_PATH = Path("week11/contamination_check.json")

PARTITIONS = {
    "train": DATASET_DIR / "train",
    "dev": DATASET_DIR / "dev",
    "held_out": DATASET_DIR / "held_out",
}

def load_partition(name, path):
    tasks = []
    if not path.exists():
        return tasks

    for file_path in sorted(path.glob("*.json")):
        with file_path.open() as f:
            task = json.load(f)

        task["_file"] = str(file_path)
        task["_partition"] = name
        tasks.append(task)

    return tasks

def normalize_text(text):
    return " ".join(text.lower().split())

def ngrams(text, n=8):
    tokens = normalize_text(text).split()
    if len(tokens) < n:
        return set()
    return set(tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1))

def task_text(task):
    input_obj = task.get("input", {})
    output_obj = task.get("candidate_output", {})

    return " ".join([
        str(input_obj.get("hiring_signal", "")),
        str(input_obj.get("bench_summary", "")),
        str(output_obj.get("subject", "")),
        str(output_obj.get("body", "")),
    ])

def main():
    partitions = {
        name: load_partition(name, path)
        for name, path in PARTITIONS.items()
    }

    all_tasks = [
        task
        for tasks in partitions.values()
        for task in tasks
    ]

    task_ids = [t.get("task_id") for t in all_tasks]
    duplicate_task_ids = [
        task_id
        for task_id, count in Counter(task_ids).items()
        if task_id and count > 1
    ]

    outputs = [
        normalize_text(t.get("candidate_output", {}).get("body", ""))
        for t in all_tasks
    ]
    duplicate_outputs = [
        output
        for output, count in Counter(outputs).items()
        if output and count > 1
    ]

    train_ngrams = set()
    for task in partitions["train"]:
        train_ngrams |= ngrams(task_text(task), n=8)

    held_out_overlaps = []
    for task in partitions["held_out"]:
        overlap = train_ngrams & ngrams(task_text(task), n=8)
        if overlap:
            held_out_overlaps.append({
                "task_id": task.get("task_id"),
                "file": task.get("_file"),
                "overlap_count": len(overlap),
                "example_overlap": " ".join(next(iter(overlap))),
            })

    same_body_cross_partition = []
    for a, b in combinations(all_tasks, 2):
        if a["_partition"] == b["_partition"]:
            continue

        body_a = normalize_text(a.get("candidate_output", {}).get("body", ""))
        body_b = normalize_text(b.get("candidate_output", {}).get("body", ""))

        if body_a and body_a == body_b:
            same_body_cross_partition.append({
                "task_a": a.get("task_id"),
                "partition_a": a["_partition"],
                "task_b": b.get("task_id"),
                "partition_b": b["_partition"],
            })

    report = {
        "summary": {
            "train_tasks": len(partitions["train"]),
            "dev_tasks": len(partitions["dev"]),
            "held_out_tasks": len(partitions["held_out"]),
            "duplicate_task_ids": len(duplicate_task_ids),
            "duplicate_outputs": len(duplicate_outputs),
            "held_out_train_8gram_overlaps": len(held_out_overlaps),
            "same_body_cross_partition": len(same_body_cross_partition),
            "status": "pass" if not duplicate_task_ids and not held_out_overlaps and not same_body_cross_partition else "review_required",
        },
        "duplicate_task_ids": duplicate_task_ids,
        "held_out_train_8gram_overlaps": held_out_overlaps,
        "same_body_cross_partition": same_body_cross_partition,
        "notes": [
            "This interim check covers duplicate task IDs, exact repeated outputs across partitions, and 8-gram overlap between train and held_out.",
            "Final submission should add embedding similarity and time-shift verification."
        ],
    }

    OUTPUT_PATH.write_text(json.dumps(report, indent=2))
    print(f"Wrote {OUTPUT_PATH}")
    print(json.dumps(report["summary"], indent=2))

if __name__ == "__main__":
    main()
