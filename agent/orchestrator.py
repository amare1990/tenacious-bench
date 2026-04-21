from __future__ import annotations

import argparse

from enrichment.crunchbase import find_company_profile
from enrichment.jobs import build_hiring_signal_brief
from enrichment.ai_maturity import score_ai_maturity
from enrichment.mock_data import (
    # get_mock_ai_maturity,
    get_mock_gap,
    get_mock_bench,
)
from agent.email_agent import generate_email


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Conversion Engine pipeline.")
    parser.add_argument("--company", required=True, help="Company name to process")
    return parser.parse_args()


def run_pipeline(company_name: str) -> None:
    company = find_company_profile(company_name)
    signals = build_hiring_signal_brief(company_name)

    # Still mocked for now
    ai = score_ai_maturity(company_name, signals)
    gap = get_mock_gap()
    bench = get_mock_bench()

    segment = "Segment 1 - Recently Funded"
    confidence = 0.8

    email = generate_email(company, signals, ai, gap)

    print("\n=== COMPANY ===")
    print(company.model_dump())

    print("\n=== SIGNALS ===")
    print(signals.model_dump())

    print("\n=== AI MATURITY ===")
    print(ai.model_dump())

    print("\n=== GAP ===")
    print(gap.model_dump())

    print("\n=== EMAIL ===")
    print("Subject:", email["subject"])
    print("Body:\n", email["body"])


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(args.company)
