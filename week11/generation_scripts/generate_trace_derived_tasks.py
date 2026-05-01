import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # week11/
REPO_ROOT = ROOT.parent                            # conversion-engine/

# Use real Conversion Engine traces first. Avoid tau2/trp1 retail eval traces for Week 11 task authoring.
TRACE_CANDIDATES = [
    REPO_ROOT / "data" / "trace_log.jsonl",       # primary: real Week 10 conversion-engine workflow traces
    REPO_ROOT / "eval" / "probes" / "probe_trace_log.json",  # fallback: probe traces if needed
    REPO_ROOT / "eval" / "trace_log.jsonl",        # last fallback: baseline eval metadata, lower value
]

OUT_DIR = ROOT / "tenacious_bench_v0.1" / "trace_generated"
OUT_DIR.mkdir(parents=True, exist_ok=True)

random.seed(43)

BANNED_PHRASES = [
    "world-class", "top talent", "A-players", "rockstar", "ninja", "wizard",
    "skyrocket", "supercharge", "10x", "I hope this email finds you well",
    "just following up", "circling back", "quick chat", "quick question",
    "synergy", "synergize", "ecosystem", "game-changer", "disruptor",
    "paradigm shift", "don't miss out", "per my last email",
]


def find_trace_file() -> Path:
    for path in TRACE_CANDIDATES:
        if path.exists() and path.stat().st_size > 0:
            return path
    raise FileNotFoundError(
        "Could not find a usable trace file. Checked:\n"
        + "\n".join(str(p) for p in TRACE_CANDIDATES)
    )


def load_jsonl(path: Path) -> list[dict]:
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"Skipping invalid JSONL line {line_num} in {path}")
    return records


def get_nested(d: dict, path: list[str]):
    cur = d
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def extract_candidate_output(record: dict) -> str | None:
    # Real data/trace_log.jsonl shapes
    email = get_nested(record, ["payload", "email"])
    if isinstance(email, dict):
        subject = email.get("subject") or ""
        body = email.get("body") or ""
        if subject or body:
            return f"Subject: {subject}\n\n{body}".strip()

    followup = record.get("followup")
    if isinstance(followup, dict):
        subject = followup.get("subject") or ""
        body = followup.get("body") or ""
        if subject or body:
            return f"Subject: {subject}\n\n{body}".strip()

    last_outbound = get_nested(record, ["conversation_state", "last_outbound_message"])
    if isinstance(last_outbound, str) and last_outbound.strip():
        return last_outbound.strip()

    # Generic fallback shapes
    for key in ["output", "final_output", "candidate_output", "email", "draft", "response", "message", "content"]:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict):
            subject = value.get("subject") or ""
            body = value.get("body") or ""
            if subject or body:
                return f"Subject: {subject}\n\n{body}".strip()

    return None


def extract_company(record: dict) -> str:
    return (
        get_nested(record, ["payload", "company_name"])
        or record.get("company_name")
        or get_nested(record, ["hubspot_result", "payload", "company_name"])
        or "Unknown Prospect"
    )


def extract_context(record: dict) -> dict:
    payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
    hubspot_payload = get_nested(record, ["hubspot_result", "payload"])
    if not isinstance(hubspot_payload, dict):
        hubspot_payload = {}

    return {
        "event_type": record.get("event_type"),
        "company": extract_company(record),
        "source_trace_id": record.get("trace_id") or record.get("timestamp_utc") or "unknown_trace",
        "hiring_signal_brief": payload.get("hiring_signal_brief") or hubspot_payload.get("hiring_signal_summary"),
        "ai_maturity_profile": payload.get("ai_maturity_profile") or {
            "score": hubspot_payload.get("ai_maturity_score"),
            "confidence": hubspot_payload.get("ai_maturity_confidence"),
            "rationale": hubspot_payload.get("ai_maturity_rationale"),
        },
        "competitor_gap_brief": payload.get("competitor_gap_brief") or hubspot_payload.get("competitor_gap_summary"),
        "bench_match_summary": payload.get("bench_match_summary") or {
            "bench_fit": hubspot_payload.get("bench_fit"),
            "bench_confidence": hubspot_payload.get("bench_confidence"),
            "bench_notes": hubspot_payload.get("bench_notes"),
        },
        "policy_result": payload.get("policy_result"),
        "reply_text": record.get("reply_text"),
        "reply_analysis": record.get("analysis"),
    }


def infer_failure_mode(text: str, context: dict) -> str:
    lower = text.lower()

    if any(p.lower() in lower for p in BANNED_PHRASES):
        return "banned_phrase"
    if "bench" in lower:
        return "external_bench_language"
    if "$" in text and any(x in lower for x in ["contract", "total", "quote", "discount"]):
        return "pricing_violation"
    if "[first name]" in lower or "[company]" in lower:
        return "generic_template"
    if any(x in lower for x in ["behind the curve", "falling behind", "catch up", "you need to", "you should"]):
        return "condescending_gap"
    if any(x in lower for x in ["series c", "$40m", "$50m"]):
        return "fabricated_signal"
    if lower.count("?") >= 3:
        return "multi_ask"
    if any(x in lower for x in ["aggressively", "must be feeling", "clearly scaling", "obvious next move"]):
        return "weak_signal_overassertion"
    if "quick observation" in lower or "working angle" in lower:
        return "generic_or_internal_language"
    if not any(str(v).lower()[:30] in lower for v in context.values() if isinstance(v, str) and len(v) > 20):
        return "missing_specific_signal_reference"
    return "trace_quality_regression"


def normalize_record(record: dict, idx: int) -> dict | None:
    candidate_output = extract_candidate_output(record)
    if not candidate_output:
        return None

    context = extract_context(record)
    failure_mode = infer_failure_mode(candidate_output, context)

    return {
        "task_id": f"trace_derived_{idx:03d}",
        "source_mode": "trace_derived",
        "failure_mode": failure_mode,
        "difficulty": "medium" if failure_mode not in {"fabricated_signal", "pricing_violation"} else "hard",
        "input": {
            **context,
            "evaluation_instruction": (
                "Score the candidate outreach against Tenacious rules: grounded signal use, confidence-aware phrasing, "
                "banned phrases, no external bench language, capacity truthfulness, pricing scope, single ask, "
                "word limit, and non-condescending framing."
            ),
        },
        "candidate_output": candidate_output,
        "rubric": {
            "max_score": 10,
            "checks": {
                "specific_signal_grounded": True,
                "confidence_aware_phrasing_required": True,
                "banned_phrase_check": True,
                "no_external_bench_language": True,
                "no_capacity_overcommitment": True,
                "no_pricing_fabrication": True,
                "single_ask": True,
                "non_condescending": True,
                "word_limit": {"cold_outreach": 120, "warm_reply": 200, "reengagement": 100},
            },
            "expected_failure": failure_mode,
        },
        "metadata": {
            "generator": "generate_trace_derived_tasks.py",
            "seed": 43,
            "version": "v0.1",
            "source": "week10_conversion_engine_trace_log",
        },
    }


def main():
    trace_file = find_trace_file()
    records = load_jsonl(trace_file)
    usable = []

    for record in records:
        task = normalize_record(record, len(usable))
        if task:
            usable.append(task)

    if not usable:
        raise ValueError(f"No usable candidate outputs found in {trace_file}")

    target_count = 60
    expanded = []
    for i in range(target_count):
        base = dict(usable[i % len(usable)])
        base["task_id"] = f"trace_derived_{i:03d}"
        base["metadata"] = dict(base.get("metadata", {}))
        base["metadata"]["expanded_from_usable_index"] = i % len(usable)
        expanded.append(base)

    for task in expanded:
        out_file = OUT_DIR / f"{task['task_id']}.json"
        with out_file.open("w", encoding="utf-8") as f:
            json.dump(task, f, indent=2, ensure_ascii=False)

    print(f"Loaded trace file: {trace_file}")
    print(f"Usable trace records: {len(usable)}")
    print(f"Generated {len(expanded)} trace-derived tasks in {OUT_DIR}")


if __name__ == "__main__":
    main()