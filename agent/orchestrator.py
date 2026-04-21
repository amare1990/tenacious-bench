from __future__ import annotations

import argparse
import time

from enrichment.crunchbase import find_company_profile
from enrichment.jobs import build_hiring_signal_brief
from enrichment.ai_maturity import score_ai_maturity
from enrichment.competitor_gap import build_competitor_gap_brief
from enrichment.bench import build_bench_match_summary
from agent.scoring import classify_icp_segment
from agent.policies import decide_outreach_policy
from agent.email_agent import generate_email
from integrations.tracing import log_trace


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Conversion Engine pipeline.")
    parser.add_argument("--company", required=True, help="Company name to process")
    return parser.parse_args()


def run_pipeline(company_name: str) -> None:
    started_at = time.perf_counter()

    company = find_company_profile(company_name)
    signals = build_hiring_signal_brief(company_name)
    ai = score_ai_maturity(company_name, signals)
    gap = build_competitor_gap_brief(company_name, ai)
    bench = build_bench_match_summary(signals, ai)

    segment_result = classify_icp_segment(company, signals, ai, gap)
    policy_result = decide_outreach_policy(segment_result, bench)

    email = None
    if policy_result["should_contact"]:
        email = generate_email(
            company=company,
            signals=signals,
            ai=ai,
            gap=gap,
            segment_result=segment_result,
            policy_result=policy_result,
        )

    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)

    trace_payload = {
        "company_name": company_name,
        "company_profile": company,
        "hiring_signal_brief": signals,
        "ai_maturity_profile": ai,
        "competitor_gap_brief": gap,
        "bench_match_summary": bench,
        "segment_result": segment_result,
        "policy_result": policy_result,
        "email": email,
        "duration_ms": duration_ms,
    }

    log_trace(event_type="prospect_pipeline_run", payload=trace_payload)

    print("\n=== COMPANY ===")
    print(company.model_dump())

    print("\n=== SIGNALS ===")
    print(signals.model_dump())

    print("\n=== AI MATURITY ===")
    print(ai.model_dump())

    print("\n=== GAP ===")
    print(gap.model_dump())

    print("\n=== SEGMENT ===")
    print(segment_result)

    print("\n=== POLICY ===")
    print(policy_result)

    if email is None:
        print("\n=== DECISION ===")
        print("Do not contact.")
    else:
        print("\n=== EMAIL ===")
        print("Subject:", email["subject"])
        print("Body:\n", email["body"])

    print("\n=== TRACE ===")
    print(f"Logged run to data/trace_log.jsonl")
    print(f"Duration: {duration_ms} ms")


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(args.company)
