import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "tenacious_bench_v0.1"
PARTITIONS = ["held_out", "dev", "train"]  # priority: keep held_out first

def candidate_key(value):
    if isinstance(value, str):
        return value.strip().lower()
    return json.dumps(value, sort_keys=True, ensure_ascii=False)

def main():
    seen = {}
    removed = []

    for part in PARTITIONS:
        for path in sorted((DATASET / part).glob("*.json")):
            with path.open("r", encoding="utf-8") as f:
                task = json.load(f)

            key = candidate_key(task.get("candidate_output", ""))

            if key in seen:
                removed.append(str(path.relative_to(ROOT)))
                path.unlink()
            else:
                seen[key] = str(path.relative_to(ROOT))

    out = DATASET / "removed_duplicates.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(removed, f, indent=2)

    print(f"Removed {len(removed)} duplicate files")
    print(f"Wrote {out}")

if __name__ == "__main__":
    main()
