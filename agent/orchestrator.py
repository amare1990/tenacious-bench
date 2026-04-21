from enrichment.mock_data import (
    get_mock_company,
    get_mock_signals,
    get_mock_ai_maturity,
    get_mock_gap,
    get_mock_bench
)

from agent.email_agent import generate_email


def run_pipeline():
    # Step 1: Enrichment
    company = get_mock_company()
    signals = get_mock_signals()
    ai = get_mock_ai_maturity()
    gap = get_mock_gap()
    bench = get_mock_bench()

    # Step 2: Simple scoring (placeholder)
    segment = "Segment 1 - Recently Funded"
    confidence = 0.8

    # Step 3: Generate email
    email = generate_email(company, signals, ai, gap)

    # Step 4: Output
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
    run_pipeline()
