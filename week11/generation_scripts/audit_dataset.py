import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "tenacious_bench_v0.1"
PARTITIONS = ["train", "dev", "held_out"]

def load_tasks():
    rows = []
    for part in PARTITIONS:
        for path in sorted((DATASET / part).glob("*.json")):
            with path.open("r", encoding="utf-8") as f:
                task = json.load(f)
            rows.append((part, path.name, task))
    return rows

def main():
    rows = load_tasks()

    print("Partition counts")
    print(Counter(part for part, _, _ in rows))
    print()

    print("Source modes")
    print(Counter(t.get("source_mode", "MISSING") for _, _, t in rows))
    print()

    print("Failure modes")
    print(Counter(t.get("failure_mode", "MISSING") for _, _, t in rows))
    print()

    print("Difficulty")
    print(Counter(t.get("difficulty", "MISSING") for _, _, t in rows))
    print()

    missing = []
    seen_outputs = Counter()

    for part, filename, task in rows:
        for key in ["task_id", "source_mode", "failure_mode", "difficulty", "input", "candidate_output", "rubric"]:
            if key not in task:
                missing.append((part, filename, key))

        candidate = task.get("candidate_output", "")

        if isinstance(candidate, str):
            key = candidate.strip().lower()
        elif isinstance(candidate, dict):
            key = json.dumps(candidate, sort_keys=True)
        else:
            key = str(candidate)

        if key:
            seen_outputs[key] += 1

    print("Missing required fields")
    if missing:
        for item in missing[:50]:
            print(item)
    else:
        print("None")
    print()

    duplicates = [text for text, count in seen_outputs.items() if count > 1]
    print(f"Exact duplicate candidate outputs: {len(duplicates)}")

    report = {
        "partition_counts": Counter(part for part, _, _ in rows),
        "source_modes": Counter(t.get("source_mode", "MISSING") for _, _, t in rows),
        "failure_modes": Counter(t.get("failure_mode", "MISSING") for _, _, t in rows),
        "difficulty": Counter(t.get("difficulty", "MISSING") for _, _, t in rows),
        "missing_required_fields": missing,
        "exact_duplicate_candidate_outputs": len(duplicates),
        "total_tasks": len(rows),
    }

    out = DATASET / "dataset_audit.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=dict)

    print()
    print(f"Wrote {out}")

if __name__ == "__main__":
    main()
