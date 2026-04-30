import json
import random
import shutil
from pathlib import Path

SEED = 42
random.seed(SEED)

INPUT_DIR = Path("week11/tenacious_bench_v0.1/seed_tasks")

TRAIN_DIR = Path("week11/tenacious_bench_v0.1/train")
DEV_DIR = Path("week11/tenacious_bench_v0.1/dev")
HELD_OUT_DIR = Path("week11/tenacious_bench_v0.1/held_out")

# ensure clean directories
for d in [TRAIN_DIR, DEV_DIR, HELD_OUT_DIR]:
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True, exist_ok=True)

def load_tasks():
    files = list(INPUT_DIR.glob("*.json"))
    tasks = []

    for f in files:
        with f.open() as fh:
            tasks.append((f, json.load(fh)))

    return tasks

def main():
    tasks = load_tasks()

    if not tasks:
        print("No tasks found in seed_tasks/")
        return

    random.shuffle(tasks)

    n = len(tasks)

    train_end = int(0.5 * n)
    dev_end = train_end + int(0.3 * n)

    train = tasks[:train_end]
    dev = tasks[train_end:dev_end]
    held_out = tasks[dev_end:]

    def copy_tasks(task_list, target_dir):
        for src_path, task in task_list:
            dst = target_dir / src_path.name
            shutil.copy(src_path, dst)

    copy_tasks(train, TRAIN_DIR)
    copy_tasks(dev, DEV_DIR)
    copy_tasks(held_out, HELD_OUT_DIR)

    print(f"Total: {n}")
    print(f"Train: {len(train)}")
    print(f"Dev: {len(dev)}")
    print(f"Held-out: {len(held_out)}")

if __name__ == "__main__":
    main()
