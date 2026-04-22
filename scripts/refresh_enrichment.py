from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.orchestrator import build_lead
from enrichment.source_inventory import json_load


DEFAULT_COMPANIES_PATH = Path(__file__).resolve().parent.parent / "data" / "companies.json"


def _load_default_companies() -> list[str]:
    records = json_load(DEFAULT_COMPANIES_PATH, [])
    names = [str(item.get("company_name")) for item in records if isinstance(item, dict) and item.get("company_name")]
    return names


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh processed enrichment briefs for one or more companies.")
    parser.add_argument("companies", nargs="*", help="Optional company names. Defaults to all companies in data/companies.json")
    args = parser.parse_args()

    companies = args.companies or _load_default_companies()
    if not companies:
        raise SystemExit("No companies provided and data/companies.json is empty.")

    results = []
    for company_name in companies:
        lead = build_lead(company_name)
        results.append(
            {
                "company_name": company_name,
                "segment": lead["segment_result"]["segment"],
                "artifact_paths": lead["artifact_paths"],
                "missing_inputs": lead["signals"].missing_inputs,
            }
        )

    print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()
