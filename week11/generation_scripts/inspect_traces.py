import json
from pathlib import Path

TRACE_PATH = Path("eval/trp1-eval/trace_log.jsonl")

with TRACE_PATH.open() as f:
    for i, line in enumerate(f):
        if i >= 5:
            break

        obj = json.loads(line)
        print("=" * 80)
        print(f"TRACE {i}")
        print(json.dumps(obj, indent=2)[:4000])
