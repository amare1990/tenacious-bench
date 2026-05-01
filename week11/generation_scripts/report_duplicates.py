import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "tenacious_bench_v0.1"
PARTITIONS = ["train", "dev", "held_out"]

def candidate_key(value):
    if isinstance(value, str):
        return value.strip().lower()
    return json.dumps(value, sort_keys=True, ensure_ascii=False)

def main():
    seen = defaultdict(list)

    for part in PARTITIONS:
        for path in sorted((DATASET / part).glob("*.json")):
            with path.open("r", encoding="utf-8") as f:
                task = json.load(f)
            key = candidate_key(task.get("candidate_output", ""))
            seen[key].append(str(path.relative_to(ROOT)))

    duplicates = {k: v for k, v in seen.items() if len(v) > 1}

    out = DATASET / "duplicate_report.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(duplicates, f, indent=2, ensure_ascii=False)

    print(f"Duplicate groups: {len(duplicates)}")
    print(f"Wrote {out}")

    for i, paths in enumerate(duplicates.values()):
        if i >= 10:
            break
        print(paths)

if __name__ == "__main__":
    main()
