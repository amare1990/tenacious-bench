import json
from pathlib import Path

INPUT_PATH = Path("data/trace_log.jsonl")
OUTPUT_DIR = Path("week11/tenacious_bench_v0.1/seed_tasks")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def infer_failure_dimension(subject, body):
    text = f"{subject}\n{body}".lower()

    if "no email generated" in text:
        return "generation_failure"

    if (
        "working angle" in text
        or "public ai readiness" in text
        or "segment 1" in text
        or "segment 2" in text
        or "segment 3" in text
        or "segment 4" in text
    ):
        return "internal_analysis_leakage"

    return "weak_grounding"

def convert_trace_to_task(trace, idx):
    payload = trace.get("payload", {})

    email = payload.get("email", {})
    subject = email.get("subject", "Context: hiring signal review")
    body = email.get("body", "No email generated. Evaluate based on inputs.")

    return {
        "task_id": f"TB-SEED-{idx:03d}",
        "source_mode": "trace_derived",
        "failure_dimension": infer_failure_dimension(subject, body),
        "input": {
            "channel": "email",
            "prospect_name": payload.get("company_name", "Unknown"),
            "company": payload.get("company_name", "Unknown"),
            "signal_confidence": "High",
            "hiring_signal": payload.get("hiring_signal_brief", {}).get("summary", ""),
            "bench_summary": str(payload.get("bench_match_summary", "")),
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
        },        
    }

def main():
    created = 0
    skipped = 0

    with INPUT_PATH.open() as f:
        for line in f:
            trace = json.loads(line)

            # only process correct event type
            if trace.get("event_type") != "prospect_pipeline_run":
                skipped += 1
                continue

            task = convert_trace_to_task(trace, created)

            output_file = OUTPUT_DIR / f"task_{created:03d}.json"

            with output_file.open("w") as out:
                json.dump(task, out, indent=2)

            print(f"Created {output_file}")
            created += 1

            if created >= 20:
                break

    print(f"Done. Created={created}, skipped={skipped}")

if __name__ == "__main__":
    main()