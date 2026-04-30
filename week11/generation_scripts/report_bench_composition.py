import json
from collections import Counter
from pathlib import Path

DATASET_DIR = Path("week11/tenacious_bench_v0.1")
REPORT_PATH = Path("week11/bench_composition.md")

PARTITIONS = ["train", "dev", "held_out", "seed_tasks", "examples"]

def load_tasks():
    tasks = []
    for partition in PARTITIONS:
        part_dir = DATASET_DIR / partition
        if not part_dir.exists():
            continue

        for path in sorted(part_dir.glob("*.json")):
            with path.open() as f:
                task = json.load(f)
            task["_partition"] = partition
            tasks.append(task)

    return tasks

def main():
    tasks = load_tasks()

    by_partition = Counter(t["_partition"] for t in tasks)
    by_source = Counter(t.get("source_mode", "unknown") for t in tasks)
    by_dimension = Counter(
        t.get("failure_dimension", "unspecified")
        for t in tasks
    )

    lines = []
    lines.append("# Bench Composition Report\n")
    lines.append(f"Total tasks counted: **{len(tasks)}**\n")

    lines.append("## By Partition\n")
    for k, v in sorted(by_partition.items()):
        lines.append(f"- {k}: {v}")

    lines.append("\n## By Source Mode\n")
    for k, v in sorted(by_source.items()):
        lines.append(f"- {k}: {v}")

    lines.append("\n## By Failure Dimension\n")
    for k, v in sorted(by_dimension.items()):
        lines.append(f"- {k}: {v}")

    REPORT_PATH.write_text("\n".join(lines))
    print(f"Wrote {REPORT_PATH}")

if __name__ == "__main__":
    main()
