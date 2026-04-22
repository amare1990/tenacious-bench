from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from datetime import date

from briefs.models import CompanyProfile


DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "companies.json"


def get_company_profile_mock(name: str) -> CompanyProfile:
    """Deterministic mock data for a vertical slice."""
    return CompanyProfile(
        company_name=name,
        website=f"https://www.{name.replace(' ', '').lower()}.com",
        industry="Software",
        employee_count=75,
        location="Remote",
        funding_stage="Series A",
        last_funding_date=date.today(),
    )


def _normalize_name(name: str) -> str:
    return " ".join(name.strip().lower().split())


def _load_company_records() -> list[dict[str, Any]]:
    if not DATA_PATH.exists():
        return []

    with DATA_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("companies.json must contain a list of company records.")

    return data


def _record_to_company_profile(record: dict[str, Any]) -> CompanyProfile:
    return CompanyProfile(
        company_name=record.get("company_name", ""),
        industry=record.get("industry"),
        employee_count=record.get("employee_count"),
        location=record.get("location"),
        funding_stage=record.get("funding_stage"),
        last_funding_date=record.get("last_funding_date"),
    )


def find_company_profile(company_name: str) -> CompanyProfile:
    """Look up a company by name from local structured data.

    Matching strategy:
    1. exact normalized match
    2. substring fallback
    If no data file exists, raises ValueError.
    """
    records = _load_company_records()
    if not records:
        raise ValueError("No local company data available (data/companies.json missing)")

    normalized_query = _normalize_name(company_name)

    exact_match: dict[str, Any] | None = None
    partial_matches: list[dict[str, Any]] = []

    for record in records:
        record_name = record.get("company_name", "")
        normalized_record_name = _normalize_name(record_name)

        if normalized_record_name == normalized_query:
            exact_match = record
            break

        if normalized_query in normalized_record_name or normalized_record_name in normalized_query:
            partial_matches.append(record)

    if exact_match is not None:
        return _record_to_company_profile(exact_match)

    if len(partial_matches) == 1:
        return _record_to_company_profile(partial_matches[0])

    if len(partial_matches) > 1:
        candidates = ", ".join(match.get("company_name", "<unknown>") for match in partial_matches)
        raise ValueError(
            f"Ambiguous company lookup for '{company_name}'. Candidates: {candidates}"
        )

    raise ValueError(f"No company found for '{company_name}'.")
