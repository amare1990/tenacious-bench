import json
import re
import sys
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

load_dotenv()

from agent.orchestrator import process_reply, send_initial_outreach



PROBE_CASES = ROOT / "eval" / "probes" / "probe_cases.jsonl"
TRACE_OUT = ROOT / "eval" / "probes" / "probe_trace_log.json"
SCORE_OUT = ROOT / "eval" / "probes" / "probe_score_log.json"

import os

os.environ.setdefault("EMAIL_MODE", "dry_run")
os.environ.setdefault("HUBSPOT_MODE", "dry_run")
os.environ.setdefault("SMS_MODE", "dry_run")
os.environ.setdefault("CALCOM_MODE", "dry_run")


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def call_agent(probe: dict) -> str:
    from agent.email_agent import generate_followup_email

    class FakeAnalysis:
        reply_type = "objection"

        def model_dump(self):
            return {
                "reply_type": self.reply_type,
                "reply_text": probe["input"],
                "probe_id": probe["id"],
                "category": probe["category"],
                "context": probe.get("context", {}),
            }

    followup = generate_followup_email(
        company_name="ProbeCo",
        analysis=FakeAnalysis(),
    )

    return f"{followup.get('subject','')}\n\n{followup.get('body','')}".strip()

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def score_probe(probe: dict, output: str) -> dict:
    """
    Minimal rule-based scorer.

    A probe fails if the output contains any failure criterion as a rough phrase match.
    This is intentionally conservative and transparent.
    """

    output_norm = normalize(output)
    failures = []

    for criterion in probe.get("failure_criteria", []):
        criterion_norm = normalize(criterion)

        # Simple keyword-ish heuristic:
        # split criterion into meaningful terms and check whether enough appear.
        terms = [
            t for t in re.findall(r"[a-z0-9_]+", criterion_norm)
            if len(t) > 3
        ]

        if not terms:
            continue

        hits = sum(1 for t in terms if t in output_norm)
        threshold = max(1, min(3, len(terms) // 2))

        if hits >= threshold:
            failures.append(criterion)

    passed = len(failures) == 0

    return {
        "probe_id": probe["id"],
        "category": probe["category"],
        "severity": probe.get("severity"),
        "passed": passed,
        "failure_count": len(failures),
        "matched_failure_criteria": failures,
    }


def summarize(scores: list[dict]) -> dict:
    total = len(scores)
    failed = [s for s in scores if not s["passed"]]

    by_category = {}
    for s in scores:
        cat = s["category"]
        by_category.setdefault(cat, {"total": 0, "failed": 0})
        by_category[cat]["total"] += 1
        if not s["passed"]:
            by_category[cat]["failed"] += 1

    for cat, stats in by_category.items():
        stats["failure_rate"] = (
            stats["failed"] / stats["total"] if stats["total"] else 0.0
        )

    return {
        "total_probes": total,
        "passed": total - len(failed),
        "failed": len(failed),
        "pass_rate": (total - len(failed)) / total if total else 0.0,
        "failure_rate": len(failed) / total if total else 0.0,
        "by_category": by_category,
    }


def main():
    probes = load_jsonl(PROBE_CASES)

    traces = []
    scores = []

    for probe in probes:
        try:
            output = call_agent(probe)
            error = None
        except Exception as e:
            output = ""
            error = str(e)

        trace = {
            "probe_id": probe["id"],
            "category": probe["category"],
            "input": probe["input"],
            "context": probe.get("context", {}),
            "output": output,
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        score = score_probe(probe, output)

        if error:
            score["passed"] = False
            score["runtime_error"] = error

        traces.append(trace)
        scores.append(score)

    summary = summarize(scores)

    TRACE_OUT.write_text(
        json.dumps(traces, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    SCORE_OUT.write_text(
        json.dumps(
            {
                "summary": summary,
                "scores": scores,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
