from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path
from typing import Any

from briefs.models import CompanyProfile
from enrichment.source_inventory import RAW_DIR, json_load, slugify_company_name


FIXTURE_PATH = Path(__file__).resolve().parent.parent / "data" / "companies.json"
RAW_CSV_PATH = RAW_DIR / "crunchbase" / "crunchbase-companies-information.csv"
RAW_JSON_EXPORT_PATH = RAW_DIR / "crunchbase" / "crunchbase_companies.json"


def get_company_profile_mock(name: str) -> CompanyProfile:
    return CompanyProfile(
        company_name=name,
        website=f"https://www.{name.replace(' ', '').lower()}.com",
        industry="Software",
        employee_count=75,
        location="Remote",
        funding_stage="Series A",
        last_funding_date=date.today(),
        slug=slugify_company_name(name),
        source="mock",
    )


def _normalize_name(name: str) -> str:
    return " ".join(name.strip().lower().split())


def _load_fixture_records() -> list[dict[str, Any]]:
    data = json_load(FIXTURE_PATH, [])
    if not isinstance(data, list):
        raise ValueError("companies.json must contain a list of company records.")
    return data


def _load_raw_csv_records() -> list[dict[str, Any]]:
    if not RAW_CSV_PATH.exists() or RAW_CSV_PATH.stat().st_size == 0:
        return []

    with RAW_CSV_PATH.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _parse_jsonish(value: str | None, default: Any) -> Any:
    if value in (None, "", "null", "NULL"):
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def _estimate_employee_count(raw_value: str | None) -> int | None:
    if not raw_value or raw_value in {"null", "NULL"}:
        return None
    text = raw_value.strip()
    if text.isdigit():
        return int(text)
    if "-" in text:
        parts = [p.strip() for p in text.split("-", 1)]
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            low, high = int(parts[0]), int(parts[1])
            return round((low + high) / 2)
    if text.endswith("+") and text[:-1].isdigit():
        return int(text[:-1])
    return None


def _parse_industry(raw_value: str | None) -> str | None:
    payload = _parse_jsonish(raw_value, None)
    if isinstance(payload, list) and payload:
        values = [str(item.get("value", "")).strip() for item in payload if isinstance(item, dict)]
        values = [value for value in values if value]
        if values:
            return ", ".join(values[:3])
    if isinstance(raw_value, str) and raw_value not in {"", "null", "NULL"}:
        return raw_value
    return None


def _parse_funding_stage(record: dict[str, Any]) -> str | None:
    funding_meta = _parse_jsonish(record.get("funding_rounds"), {})
    if isinstance(funding_meta, dict):
        stage = funding_meta.get("last_funding_type")
        if stage:
            return str(stage)
    return record.get("stage") or None


def _parse_last_funding_date(record: dict[str, Any]) -> str | None:
    funding_meta = _parse_jsonish(record.get("funding_rounds"), {})
    if isinstance(funding_meta, dict):
        last_funding_at = funding_meta.get("last_funding_at")
        if last_funding_at:
            return str(last_funding_at)

    rounds = _parse_jsonish(record.get("funding_rounds_list"), [])
    if isinstance(rounds, list) and rounds:
        announced_on = rounds[-1].get("announced_on") if isinstance(rounds[-1], dict) else None
        if announced_on:
            return str(announced_on)
    return None


def _record_to_company_profile(record: dict[str, Any], source: str) -> CompanyProfile:
    company_name = record.get("company_name") or record.get("name") or ""
    website = record.get("website") or None
    location_parts = [record.get("location"), record.get("region"), record.get("country_code")]
    location = ", ".join([str(part) for part in location_parts if part]) or None
    source_record_id = record.get("source_record_id") or record.get("id") or record.get("uuid")

    return CompanyProfile(
        company_name=company_name,
        website=website,
        industry=record.get("industry") or _parse_industry(record.get("industries")),
        employee_count=record.get("employee_count") or _estimate_employee_count(record.get("num_employees")),
        location=location,
        funding_stage=record.get("funding_stage") or _parse_funding_stage(record),
        last_funding_date=record.get("last_funding_date") or _parse_last_funding_date(record),
        slug=record.get("slug") or slugify_company_name(company_name),
        source=source,
        source_record_id=str(source_record_id) if source_record_id else None,
        source_paths=[str((RAW_CSV_PATH if source == "crunchbase_raw_csv" else FIXTURE_PATH).relative_to(Path(__file__).resolve().parent.parent))],
        raw_attributes={
            key: value
            for key, value in record.items()
            if key not in {"company_name", "industry", "employee_count", "location", "funding_stage", "last_funding_date", "slug"}
            and value not in (None, "")
        },
    )


def _find_exact_record(records: list[dict[str, Any]], company_name: str) -> dict[str, Any] | None:
    normalized_query = _normalize_name(company_name)
    for record in records:
        record_name = record.get("company_name") or record.get("name") or ""
        if _normalize_name(record_name) == normalized_query:
            return record
    return None


def _find_partial_record(records: list[dict[str, Any]], company_name: str) -> dict[str, Any] | None:
    normalized_query = _normalize_name(company_name)
    if len(normalized_query) < 6:
        return None

    partial_matches: list[dict[str, Any]] = []
    for record in records:
        record_name = record.get("company_name") or record.get("name") or ""
        normalized_record_name = _normalize_name(record_name)
        if normalized_query in normalized_record_name or normalized_record_name in normalized_query:
            partial_matches.append(record)

    if len(partial_matches) == 1:
        return partial_matches[0]
    if len(partial_matches) > 1:
        candidates = ", ".join(match.get("company_name") or match.get("name") or "<unknown>" for match in partial_matches[:10])
        raise ValueError(f"Ambiguous company lookup for '{company_name}'. Candidates: {candidates}")
    return None


def _refresh_raw_json_export(raw_records: list[dict[str, Any]]) -> None:
    if not raw_records:
        return
    if RAW_JSON_EXPORT_PATH.exists() and RAW_JSON_EXPORT_PATH.stat().st_size > 0:
        return

    export_rows: list[dict[str, Any]] = []
    for record in raw_records[:250]:
        export_rows.append(
            {
                "company_name": record.get("name"),
                "slug": slugify_company_name(record.get("name", "company")),
                "industry": _parse_industry(record.get("industries")),
                "employee_count": _estimate_employee_count(record.get("num_employees")),
                "location": ", ".join([part for part in [record.get("region"), record.get("country_code")] if part]) or None,
                "website": record.get("website") or None,
                "funding_stage": _parse_funding_stage(record),
                "last_funding_date": _parse_last_funding_date(record),
                "source_record_id": record.get("id") or record.get("uuid"),
            }
        )

    RAW_JSON_EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RAW_JSON_EXPORT_PATH.open("w", encoding="utf-8") as f:
        json.dump(export_rows, f, ensure_ascii=False, indent=2)
        f.write("\n")


def find_company_profile(company_name: str) -> CompanyProfile:
    raw_records = _load_raw_csv_records()
    _refresh_raw_json_export(raw_records)

    raw_exact = _find_exact_record(raw_records, company_name)
    if raw_exact is not None:
        return _record_to_company_profile(raw_exact, source="crunchbase_raw_csv")

    fixture_records = _load_fixture_records()
    if not fixture_records:
        raise ValueError("No local company data available from raw Crunchbase or data/companies.json")

    fixture_exact = _find_exact_record(fixture_records, company_name)
    if fixture_exact is not None:
        return _record_to_company_profile(fixture_exact, source="fixture_companies_json")

    fixture_partial = _find_partial_record(fixture_records, company_name)
    if fixture_partial is not None:
        return _record_to_company_profile(fixture_partial, source="fixture_companies_json")

    raw_partial = _find_partial_record(raw_records, company_name)
    if raw_partial is not None:
        return _record_to_company_profile(raw_partial, source="crunchbase_raw_csv")

    raise ValueError(f"No company found for '{company_name}'.")
