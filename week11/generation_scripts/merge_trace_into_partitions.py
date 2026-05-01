import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

GEN_DIR = ROOT / "tenacious_bench_v0.1" / "trace_generated"
TRAIN_DIR = ROOT / "tenacious_bench_v0.1" / "train"
DEV_DIR = ROOT / "tenacious_bench_v0.1" / "dev"
HELD_OUT_DIR = ROOT / "tenacious_bench_v0.1" / "held_out"

for d in [TRAIN_DIR, DEV_DIR, HELD_OUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def next_task_index(*dirs):
    max_idx = -1
    for d in dirs:
        for file in d.glob("task_*.json"):
            try:
                idx = int(file.stem.replace("task_", ""))
                max_idx = max(max_idx, idx)
            except ValueError:
                pass
    return max_idx + 1


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    generated = sorted(GEN_DIR.glob("trace_derived_*.json"))

    if not generated:
        raise FileNotFoundError(
            f"No trace-derived tasks found in {GEN_DIR}. "
            "Run generate_trace_derived_tasks.py first."
        )

    start_idx = next_task_index(TRAIN_DIR, DEV_DIR, HELD_OUT_DIR)

    # For 60 trace-derived tasks:
    # 36 train, 16 dev, 8 held_out
    split_plan = {
        "train": 36,
        "dev": 16,
        "held_out": 8,
    }

    destinations = (
        [TRAIN_DIR] * split_plan["train"]
        + [DEV_DIR] * split_plan["dev"]
        + [HELD_OUT_DIR] * split_plan["held_out"]
    )

    for offset, (src, dest_dir) in enumerate(zip(generated, destinations)):
        task = load_json(src)
        new_idx = start_idx + offset
        new_task_id = f"task_{new_idx:03d}"

        task["task_id"] = new_task_id
        task.setdefault("metadata", {})
        task["metadata"]["original_generated_id"] = src.stem
        task["metadata"]["merged_by"] = "merge_trace_into_partitions.py"
        task["metadata"]["partition"] = dest_dir.name

        out_path = dest_dir / f"{new_task_id}.json"
        save_json(out_path, task)

    print("Merged trace-derived tasks:")
    print(f"  train:    {split_plan['train']}")
    print(f"  dev:      {split_plan['dev']}")
    print(f"  held_out: {split_plan['held_out']}")
    print(f"  total:    {sum(split_plan.values())}")


if __name__ == "__main__":
    main()
