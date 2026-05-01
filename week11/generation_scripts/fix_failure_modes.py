import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "tenacious_bench_v0.1"

PARTITIONS = ["train", "dev", "held_out"]

MAP = {
    "missing_specific_signal_reference": "missing_signal_reference",
    "missing_signal_reference": "missing_signal_reference",
    "generic_or_internal_language": "generic_template",
    "MISSING": "missing_signal_reference",
}

DEFAULT = "missing_signal_reference"


def normalize(fm):
    if not fm:
        return DEFAULT
    return MAP.get(fm, fm)


def main():
    for part in PARTITIONS:
        for path in (DATASET / part).glob("*.json"):
            with path.open() as f:
                task = json.load(f)

            fm = task.get("failure_mode")
            task["failure_mode"] = normalize(fm)

            if "difficulty" not in task or task["difficulty"] == "MISSING":
                task["difficulty"] = "medium"

            with path.open("w") as f:
                json.dump(task, f, indent=2)

    print("Failure modes normalized")


if __name__ == "__main__":
    main()
