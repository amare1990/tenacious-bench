import json
import math
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

EMBEDDING_THRESHOLD = 0.85
NGRAM_SIZE = 8


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

def get_text_field(obj, key, default=""):
    if isinstance(obj, dict):
        return obj.get(key, default)
    if isinstance(obj, str):
        return obj
    return default


def normalize_text(text):
    return " ".join(str(text).lower().split())


def ngrams(text, n=NGRAM_SIZE):
    tokens = normalize_text(text).split()
    if len(tokens) < n:
        return set()
    return set(tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1))


def simple_embedding(text):
    return Counter(normalize_text(text).split())


def cosine_sim(a, b):
    common = set(a) & set(b)
    dot = sum(a[w] * b[w] for w in common)

    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


def task_text(task):
    input_obj = task.get("input", {})
    output_obj = task.get("candidate_output", {})

    if isinstance(input_obj, str):
        input_text = input_obj
    elif isinstance(input_obj, dict):
        input_text = " ".join([
            str(input_obj.get("hiring_signal", "")),
            str(input_obj.get("bench_summary", "")),
            str(input_obj.get("company_context", "")),
            str(input_obj.get("public_signal_window", "")),
        ])
    else:
        input_text = ""

    if isinstance(output_obj, str):
        output_text = output_obj
    elif isinstance(output_obj, dict):
        output_text = " ".join([
            str(output_obj.get("subject", "")),
            str(output_obj.get("body", "")),
        ])
    else:
        output_text = ""

    return f"{input_text} {output_text}"


def time_shift_ok(task):
    """
    Time-shift validation placeholder.

    For public-data tasks, this should verify that any public signals used
    by the task fall inside the declared signal window and before the
    held-out evaluation cutoff.
    """
    input_obj = task.get("input", {})
    signal_window = input_obj.get("public_signal_window")

    if signal_window is None:
        return True

    if isinstance(signal_window, dict):
        return bool(signal_window.get("start") and signal_window.get("end"))

    return True


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
        normalize_text(get_text_field(t.get("candidate_output", {}), "body", ""))
        for t in all_tasks
    ]
    duplicate_outputs = [
        output
        for output, count in Counter(outputs).items()
        if output and count > 1
    ]

    train_ngrams = set()
    for task in partitions["train"]:
        train_ngrams |= ngrams(task_text(task), n=NGRAM_SIZE)

    held_out_overlaps = []
    for task in partitions["held_out"]:
        overlap = train_ngrams & ngrams(task_text(task), n=NGRAM_SIZE)
        if overlap:
            held_out_overlaps.append(
                {
                    "task_id": task.get("task_id"),
                    "file": task.get("_file"),
                    "overlap_count": len(overlap),
                    "example_overlap": " ".join(next(iter(overlap))),
                }
            )

    embedding_overlaps = []
    for heldout_task in partitions["held_out"]:
        heldout_text = task_text(heldout_task)
        heldout_emb = simple_embedding(heldout_text)

        for train_task in partitions["train"]:
            train_text = task_text(train_task)
            sim = cosine_sim(heldout_emb, simple_embedding(train_text))

            if sim > EMBEDDING_THRESHOLD:
                embedding_overlaps.append(
                    {
                        "task_id": heldout_task.get("task_id"),
                        "file": heldout_task.get("_file"),
                        "train_task_id": train_task.get("task_id"),
                        "train_file": train_task.get("_file"),
                        "similarity": round(sim, 3),
                        "threshold": EMBEDDING_THRESHOLD,
                    }
                )

    time_shift_violations = [
        {
            "task_id": task.get("task_id"),
            "file": task.get("_file"),
        }
        for task in all_tasks
        if not time_shift_ok(task)
    ]

    same_body_cross_partition = []
    for a, b in combinations(all_tasks, 2):
        if a["_partition"] == b["_partition"]:
            continue

        body_a = normalize_text(get_text_field(a.get("candidate_output", {}), "body", ""))
        body_b = normalize_text(get_text_field(b.get("candidate_output", {}), "body", ""))

        if body_a and body_a == body_b:
            same_body_cross_partition.append(
                {
                    "task_a": a.get("task_id"),
                    "partition_a": a["_partition"],
                    "task_b": b.get("task_id"),
                    "partition_b": b["_partition"],
                }
            )

    review_required = any(
        [
            duplicate_task_ids,
            held_out_overlaps,
            same_body_cross_partition,
            embedding_overlaps,
            time_shift_violations,
        ]
    )

    report = {
        "summary": {
            "train_tasks": len(partitions["train"]),
            "dev_tasks": len(partitions["dev"]),
            "held_out_tasks": len(partitions["held_out"]),
            "duplicate_task_ids": len(duplicate_task_ids),
            "duplicate_outputs": len(duplicate_outputs),
            "held_out_train_8gram_overlaps": len(held_out_overlaps),
            "embedding_overlaps": len(embedding_overlaps),
            "time_shift_violations": len(time_shift_violations),
            "same_body_cross_partition": len(same_body_cross_partition),
            "status": "review_required" if review_required else "pass",
        },
        "duplicate_task_ids": duplicate_task_ids,
        "duplicate_outputs": duplicate_outputs,
        "held_out_train_8gram_overlaps": held_out_overlaps,
        "embedding_overlaps": embedding_overlaps,
        "time_shift_violations": time_shift_violations,
        "same_body_cross_partition": same_body_cross_partition,
        "notes": [
            "Checks train/dev/held_out partitions under week11/tenacious_bench_v0.1.",
            "Implements 8-gram overlap detection between train and held_out input/output text.",
            "Implements lightweight cosine similarity with threshold 0.85 as a cheap embedding-style contamination screen.",
            "Implements time-shift validation hook using public_signal_window metadata when available.",
            "Writes a structured contamination report to week11/contamination_check.json.",
        ],
    }

    OUTPUT_PATH.write_text(json.dumps(report, indent=2))
    print(f"Wrote {OUTPUT_PATH}")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()