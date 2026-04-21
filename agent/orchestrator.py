from __future__ import annotations

import argparse

from enrichment.crunchbase import find_company_profile
from enrichment.jobs import build_hiring_signal_brief
from enrichment.ai_maturity import score_ai_maturity
from enrichment.competitor_gap import build_competitor_gap_brief
from enrichment.mock_data import get_mock_bench
from agent.scoring import classify_icp_segment
from agent.policies import decide_outreach_policy
from agent.email_agent import generate_email


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Conversion Engine pipeline.")
    parser.add_argument("--company", required=True, help="Company name to process")
    return parser.parse_args()


def run_pipeline(company_name: str) -> None:
    company = find_company_profile(company_name)
    signals = build_hiring_signal_brief(company_name)
    ai = score_ai_maturity(company_name, signals)
    gap = build_competitor_gap_brief(company_name, ai)

    # still mocked for now
    bench = get_mock_bench()

    segment_result = classify_icp_segment(company, signals, ai, gap)
    policy_result = decide_outreach_policy(segment_result, bench)

    if not policy_result["should_contact"]:
        print("\n=== DECISION ===")
        print("Do not contact.")
        print(policy_result["reason"])
        return

    email = generate_email(
        company=company,
        signals=signals,
        ai=ai,
        gap=gap,
        segment_result=segment_result,
        policy_result=policy_result,
    )

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

    print("\n=== EMAIL ===")
    print("Subject:", email["subject"])
    print("Body:\n", email["body"])


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(args.company)
