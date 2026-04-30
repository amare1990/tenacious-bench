import json
from pathlib import Path

paths = [
    Path("eval/trp1-eval/trace_log.jsonl"),
    Path("eval/trace_log.jsonl"),
    Path("data/trace_log.jsonl"),
]

for path in paths:
    print("\n" + "#" * 100)
    print(path)

    if not path.exists():
        print("MISSING")
        continue

    with path.open() as f:
        for i, line in enumerate(f):
            if i >= 3:
                break
            obj = json.loads(line)
            print("=" * 80)
            print(f"TRACE {i}")
            print(json.dumps(obj, indent=2)[:6000])
