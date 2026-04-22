"""AI maturity scoring stubs.

Provides a small mock scorer used by the demo plus a file-backed scoring
implementation used for richer integration tests.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from briefs.models import AIMaturityProfile, HiringSignalBrief


DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "ai_signals.json"


def score_ai_maturity_mock(company_name: str, job_signal: dict) -> AIMaturityProfile:
    # Very simple deterministic scoring based on open_roles
    open_roles = job_signal.get("open_roles", 0)
    if open_roles >= 10:
        score = 3
        conf = 0.9
    elif open_roles >= 5:
        score = 2
        conf = 0.7
    elif open_roles >= 1:
        score = 1
        conf = 0.5
    else:
        score = 0
        conf = 0.3

    evidence = [f"{open_roles} engineering roles observed"]
    return AIMaturityProfile(score=score, evidence=evidence, confidence=conf,
                             rationale="mock rule: open roles -> score")


def _normalize_name(name: str) -> str:
    return " ".join(name.strip().lower().split())


def _load_ai_records() -> list[dict[str, Any]]:
    if not DATA_PATH.exists():
        return []

    with DATA_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("ai_signals.json must contain a list of AI signal records.")

    return data


def _find_ai_record(company_name: str) -> dict[str, Any]:
    normalized_query = _normalize_name(company_name)
    records = _load_ai_records()

    for record in records:
        record_name = record.get("company_name", "")
        if _normalize_name(record_name) == normalized_query:
            return record

    raise ValueError(f"No AI signal record found for '{company_name}'.")


def _compute_weighted_score(record: dict[str, Any], signals: HiringSignalBrief) -> tuple[int, float, str]:
    score_points = 0.0
    confidence = 0.35
    rationale_parts: list[str] = []

    ai_roles = int(record.get("ai_roles", 0) or 0)
    has_ai_leadership = bool(record.get("has_ai_leadership", False))
    github_ai_activity = bool(record.get("github_ai_activity", False))
    executive_ai_commentary = bool(record.get("executive_ai_commentary", False))
    modern_ml_stack = bool(record.get("modern_ml_stack", False))
    strategic_ai_mentions = bool(record.get("strategic_ai_mentions", False))

    if ai_roles >= 3:
        score_points += 1.0
        confidence += 0.15
        rationale_parts.append("Multiple AI-adjacent roles are open.")
    elif ai_roles >= 1:
        score_points += 0.5
        confidence += 0.10
        rationale_parts.append("At least one AI-adjacent role is open.")

    if has_ai_leadership:
        score_points += 1.0
        confidence += 0.15
        rationale_parts.append("Named AI/ML leadership is publicly visible.")

    if github_ai_activity:
        score_points += 0.5
        confidence += 0.08
        rationale_parts.append("Public GitHub activity suggests AI-related work.")

    if executive_ai_commentary:
        score_points += 0.5
        confidence += 0.08
        rationale_parts.append("Executive commentary references AI strategically.")

    if modern_ml_stack:
        score_points += 0.3
        confidence += 0.05
        rationale_parts.append("Modern data/ML tooling signals are present.")

    if strategic_ai_mentions:
        score_points += 0.2
        confidence += 0.04
        rationale_parts.append("Strategic communications mention AI direction.")

    tech_stack_signal = signals.tech_stack_signal or ""
    hiring_signal = signals.hiring_velocity_signal or ""

    if "data" in tech_stack_signal.lower() or "ml" in tech_stack_signal.lower():
        score_points += 0.2
        confidence += 0.03
        rationale_parts.append("Tech-stack signal reinforces AI/data readiness.")

    if "engineering" in hiring_signal.lower():
        confidence += 0.02

    if score_points < 0.5:
        maturity_score = 0
    elif score_points < 1.2:
        maturity_score = 1
    elif score_points < 2.2:
        maturity_score = 2
    else:
        maturity_score = 3

    confidence = min(round(confidence, 2), 0.95)

    if not rationale_parts:
        rationale_parts.append("No strong public AI signals were identified.")

    rationale = " ".join(rationale_parts)
    return maturity_score, confidence, rationale


def score_ai_maturity(company_name: str, signals: HiringSignalBrief) -> AIMaturityProfile:
    record = _find_ai_record(company_name)
    evidence = record.get("evidence", [])

    if not isinstance(evidence, list):
        raise ValueError(f"Invalid evidence list for '{company_name}'.")

    score, confidence, rationale = _compute_weighted_score(record, signals)

    return AIMaturityProfile(
        score=score,
        evidence=evidence,
        confidence=confidence,
        rationale=rationale,
    )
