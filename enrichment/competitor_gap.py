from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from briefs.models import CompetitorGapBrief, AIMaturityProfile


DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "competitor_signals.json"


def _normalize_name(name: str) -> str:
    return " ".join(name.strip().lower().split())


def _load_competitor_records() -> list[dict[str, Any]]:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Competitor signal data file not found at {DATA_PATH}. "
            "Create data/competitor_signals.json first."
        )

    with DATA_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("competitor_signals.json must contain a list of records.")

    return data


def _find_competitor_record(company_name: str) -> dict[str, Any]:
    normalized_query = _normalize_name(company_name)
    records = _load_competitor_records()

    for record in records:
        record_name = record.get("company_name", "")
        if _normalize_name(record_name) == normalized_query:
            return record

    raise ValueError(f"No competitor signal record found for '{company_name}'.")


def _compute_missing_practices(
    top_quartile_practices: list[str],
    observed_practices: list[str],
) -> list[str]:
    observed_set = {practice.strip().lower() for practice in observed_practices}
    missing: list[str] = []

    for practice in top_quartile_practices:
        if practice.strip().lower() not in observed_set:
            missing.append(practice)

    return missing


def _build_summary(
    company_name: str,
    peer_group: list[str],
    missing_practices: list[str],
    ai_profile: AIMaturityProfile,
) -> str:
    if not missing_practices:
        return (
            f"{company_name} appears broadly aligned with the strongest public practices "
            f"observed across peers such as {', '.join(peer_group)}."
        )

    gap_text = ", ".join(missing_practices[:2])
    readiness_text = (
        "The company appears ready for a capability-gap conversation."
        if ai_profile.score >= 2
        else "The company shows only limited AI readiness, so any gap framing should remain exploratory."
    )

    return (
        f"Compared with peers such as {', '.join(peer_group)}, {company_name} appears to be missing "
        f"public signals for {gap_text}. {readiness_text}"
    )


def build_competitor_gap_brief(
    company_name: str,
    ai_profile: AIMaturityProfile,
) -> CompetitorGapBrief:
    record = _find_competitor_record(company_name)

    peer_group = record.get("peer_group", [])
    top_quartile_practices = record.get("top_quartile_practices", [])
    observed_practices = record.get("observed_practices", [])

    if not all(isinstance(x, list) for x in [peer_group, top_quartile_practices, observed_practices]):
        raise ValueError(
            f"Invalid competitor gap record for '{company_name}'. "
            "Expected peer_group, top_quartile_practices, and observed_practices to be lists."
        )

    missing_practices = _compute_missing_practices(
        top_quartile_practices=top_quartile_practices,
        observed_practices=observed_practices,
    )

    base_confidence = 0.55
    if len(peer_group) >= 3:
        base_confidence += 0.1
    if len(top_quartile_practices) >= 2:
        base_confidence += 0.1
    if ai_profile.confidence >= 0.75:
        base_confidence += 0.05

    confidence = min(round(base_confidence, 2), 0.9)

    summary = _build_summary(
        company_name=company_name,
        peer_group=peer_group,
        missing_practices=missing_practices,
        ai_profile=ai_profile,
    )

    return CompetitorGapBrief(
        peer_group=peer_group,
        top_quartile_practices=top_quartile_practices,
        missing_practices=missing_practices,
        confidence=confidence,
        summary=summary,
    )
