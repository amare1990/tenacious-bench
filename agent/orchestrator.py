from __future__ import annotations

import argparse

from enrichment.crunchbase import find_company_profile
from enrichment.mock_data import (
    get_mock_signals,
    get_mock_ai_maturity,
    get_mock_gap,
    get_mock_bench,
)
from agent.email_agent import generate_email


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Conversion Engine pipeline.")
    parser.add_argument("--company", required=True, help="Company name to process")
    return parser.parse_args()


def run_pipeline(company_name: str) -> None:
    # Step 1: Real company lookup
    company = find_company_profile(company_name)

    # Step 2: Still mocked for now
    signals = get_mock_signals()
    ai = get_mock_ai_maturity()
    gap = get_mock_gap()
    bench = get_mock_bench()

    # Step 3: Placeholder scoring
    segment = "Segment 1 - Recently Funded"
    confidence = 0.8

    # Step 4: Email generation
    email = generate_email(company, signals, ai, gap)

    print("\n=== COMPANY ===")
    print(company.model_dump())

    print("\n=== SIGNALS ===")
    print(signals.summary)

    print("\n=== AI MATURITY ===")
    print(ai.score, ai.rationale)

    print("\n=== GAP ===")
    print(gap.summary)

    print("\n=== EMAIL ===")
    print("Subject:", email["subject"])
    print("Body:\n", email["body"])


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(args.company)
