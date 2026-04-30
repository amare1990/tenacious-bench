import json
from pathlib import Path

INPUT_PATH = Path("data/trace_log.jsonl")
OUTPUT_DIR = Path("week11/tenacious_bench_v0.1/seed_tasks")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def convert_trace_to_task(trace, idx):
    payload = trace["payload"]

    email = payload.get("email", {})

    subject = email.get("subject", "Context: hiring signal review")
    body = email.get("body", "No email generated. Evaluate based on inputs.")

    return {
        "task_id": f"TB-SEED-{idx:03d}",
        "source_mode": "trace_derived",
        "input": {
            "channel": "email",
            "prospect_name": payload.get("company_name", "Unknown"),
            "company": payload.get("company_name", "Unknown"),
            "signal_confidence": "High",
            "hiring_signal": payload["hiring_signal_brief"]["summary"],
            "bench_summary": str(payload["bench_match_summary"]),
            "calendar_link": "gettenacious.com/yabi"
        },
        "candidate_output": {
            "subject": subject,
            "body": body
        },
        "rubric": {
            "max_body_words": 120,
            "max_subject_chars": 60,
            "requires_specific_signal": True,
            "forbid_bench_word": True,
            "requires_one_ask": True,
            "requires_no_banned_phrases": True
        }
    }

def has_required_fields(trace):
    payload = trace.get("payload", {})

    if trace.get("event_type") != "prospect_pipeline_run":
        return False

    if "hiring_signal_brief" not in payload:
        return False

    if "bench_match_summary" not in payload:
        return False

    # email is optional now
    return True

def main():
    created = 0
    skipped = 0

    with INPUT_PATH.open() as f:
        for i, line in enumerate(f):
            if created >= 20:
                break

            trace = json.loads(line)

            # print("Checking trace...")
            # print(trace.get("event_type"))
            # print(trace.get("payload", {}).keys())

            if not has_required_fields(trace):
                skipped += 1
                continue

            task = convert_trace_to_task(trace, created)

            output_file = OUTPUT_DIR / f"task_{created:03d}.json"

            with output_file.open("w") as out:
                json.dump(task, out, indent=2)

            print(f"Created {output_file}")
            created += 1

    print(f"Done. Created={created}, skipped={skipped}")