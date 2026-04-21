from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from briefs.models import HiringSignalBrief


DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "company_signals.json"


def _normalize_name(name: str) -> str:
    return " ".join(name.strip().lower().split())


def _load_signal_records() -> list[dict[str, Any]]:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Signal data file not found at {DATA_PATH}. "
            "Create data/company_signals.json first."
        )

    with DATA_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("company_signals.json must contain a list of signal records.")

    return data


def _build_summary(record: dict[str, Any]) -> str:
    parts: list[str] = []

    funding = record.get("funding_signal")
    hiring = record.get("hiring_velocity_signal")
    layoffs = record.get("layoffs_signal")
    leadership = record.get("leadership_change_signal")
    tech_stack = record.get("tech_stack_signal")

    if funding:
        parts.append(funding)
    if hiring:
        parts.append(hiring)
    if layoffs:
        parts.append(layoffs)
    if leadership:
        parts.append(leadership)
    if tech_stack:
        parts.append(tech_stack)

    if not parts:
        return "No strong public hiring or operating signals were found."

    return "; ".join(parts)


def build_hiring_signal_brief(company_name: str) -> HiringSignalBrief:
    normalized_query = _normalize_name(company_name)
    records = _load_signal_records()

    match: dict[str, Any] | None = None

    for record in records:
        record_name = record.get("company_name", "")
        if _normalize_name(record_name) == normalized_query:
            match = record
            break

    if match is None:
        raise ValueError(f"No hiring signal record found for '{company_name}'.")

    confidence_by_signal = match.get("confidence_by_signal", {})
    if not isinstance(confidence_by_signal, dict):
        raise ValueError(
            f"Invalid confidence_by_signal for '{company_name}'. Expected an object."
        )

    return HiringSignalBrief(
        funding_signal=match.get("funding_signal"),
        hiring_velocity_signal=match.get("hiring_velocity_signal"),
        layoffs_signal=match.get("layoffs_signal"),
        leadership_change_signal=match.get("leadership_change_signal"),
        tech_stack_signal=match.get("tech_stack_signal"),
        confidence_by_signal=confidence_by_signal,
        summary=_build_summary(match),
    )
