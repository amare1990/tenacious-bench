"""Competitor-gap enrichment.

Builds a competitor_gap_brief.json-style object that turns outbound from a
generic vendor pitch into a research-backed gap finding.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from briefs.models import AIMaturityProfile, CompetitorGapBrief


DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "competitor_signals.json"


def competitor_gap_mock(company_name: str) -> CompetitorGapBrief:
    return CompetitorGapBrief(
        peer_group=[
            f"{company_name} Competitor A",
            f"{company_name} Competitor B",
            f"{company_name} Competitor C",
            f"{company_name} Competitor D",
            f"{company_name} Competitor E",
        ],
        top_quartile_practices=[
            "Dedicated MLOps ownership",
            "Public AI roadmap",
            "Modern data platform signals",
        ],
        missing_practices=["Dedicated MLOps ownership"],
        confidence=0.6,
        summary="Mock competitor gap: suggests MLOps and public AI-roadmap improvements.",
        sector="mock",
        company_size_band="unknown",
        observed_practices=["Modern data platform signals"],
        distribution_percentile=40.0,
        practice_evidence=[
            {
                "practice": "Dedicated MLOps ownership",
                "evidence": "Peer job posts mention MLOps / ML platform ownership.",
                "source": "mock",
                "confidence": 0.6,
            }
        ],
        sparse_sector_warning=None,
    )


def _normalize_name(name: str) -> str:
    return " ".join(name.strip().lower().split())


def _load_competitor_records() -> list[dict[str, Any]]:
    if not DATA_PATH.exists():
        return []

    with DATA_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("competitor_signals.json must contain a list of records.")

    return data


def _find_competitor_record(company_name: str) -> dict[str, Any]:
    normalized_query = _normalize_name(company_name)

    for record in _load_competitor_records():
        record_name = record.get("company_name", "")
        if _normalize_name(record_name) == normalized_query:
            return record

    raise ValueError(f"No competitor signal record found for '{company_name}'.")


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in _as_list(value) if str(item).strip()]


def _compute_missing_practices(
    top_quartile_practices: list[str],
    observed_practices: list[str],
) -> list[str]:
    observed_set = {practice.strip().lower() for practice in observed_practices}

    return [
        practice
        for practice in top_quartile_practices
        if practice.strip().lower() not in observed_set
    ]


def _score_peer_ai_maturity(peer: dict[str, Any]) -> int:
    """Apply the same 0–3 AI maturity concept to peer records.

    This is intentionally deterministic because competitor_signals.json already
    contains normalized public signals rather than live scraped pages.
    """
    if "ai_maturity_score" in peer:
        try:
            return max(0, min(3, int(peer["ai_maturity_score"])))
        except (TypeError, ValueError):
            pass

    practices = _string_list(peer.get("practices"))
    evidence = _string_list(peer.get("evidence"))
    roles = _string_list(peer.get("ai_roles"))
    tools = _string_list(peer.get("tools"))

    score = 0
    if roles:
        score += 1
    if practices or tools:
        score += 1
    if evidence and len(evidence) >= 2:
        score += 1

    return max(0, min(3, score))


def _score_target_ai_maturity(ai_profile: AIMaturityProfile) -> int:
    return max(0, min(3, int(ai_profile.score)))


def _compute_distribution_percentile(
    target_score: int,
    peer_scores: list[int],
) -> float | None:
    if not peer_scores:
        return None

    below_or_equal = sum(1 for score in peer_scores if score <= target_score)
    return round((below_or_equal / len(peer_scores)) * 100, 1)


def _extract_practice_evidence(
    missing_practices: list[str],
    record: dict[str, Any],
) -> list[dict[str, Any]]:
    evidence_by_practice = record.get("practice_evidence", {})
    result: list[dict[str, Any]] = []

    for practice in missing_practices[:3]:
        raw = None

        if isinstance(evidence_by_practice, dict):
            raw = evidence_by_practice.get(practice)

        if isinstance(raw, dict):
            result.append(
                {
                    "practice": practice,
                    "evidence": raw.get("evidence") or raw.get("summary"),
                    "source": raw.get("source") or raw.get("source_path"),
                    "peer": raw.get("peer"),
                    "confidence": float(raw.get("confidence", 0.65)),
                }
            )
        elif isinstance(raw, list):
            result.append(
                {
                    "practice": practice,
                    "evidence": "; ".join(str(item) for item in raw[:3]),
                    "source": "competitor_signals.json",
                    "peer": None,
                    "confidence": 0.65,
                }
            )
        else:
            result.append(
                {
                    "practice": practice,
                    "evidence": (
                        "Practice appears in top_quartile_practices but not in "
                        "the target company's observed_practices."
                    ),
                    "source": "data/competitor_signals.json",
                    "peer": None,
                    "confidence": 0.55,
                }
            )

    return result


def _build_summary(
    company_name: str,
    peer_group: list[str],
    missing_practices: list[str],
    ai_profile: AIMaturityProfile,
    distribution_percentile: float | None,
    sparse_sector_warning: str | None,
) -> str:
    peer_text = ", ".join(peer_group[:5])

    if sparse_sector_warning:
        return (
            f"Peer coverage is sparse for {company_name}; use the competitor-gap finding "
            "as directional research rather than a hard benchmark."
        )

    percentile_text = (
        f"estimated around the {distribution_percentile}th percentile of this peer set"
        if distribution_percentile is not None
        else "not enough peer-score data to compute a percentile"
    )

    if not missing_practices:
        return (
            f"{company_name} appears broadly aligned with public AI practices observed "
            f"across peers such as {peer_text}; the target is {percentile_text}."
        )

    gap_text = ", ".join(missing_practices[:2])

    readiness_text = (
        "The company appears ready for a capability-gap conversation."
        if ai_profile.score >= 2
        else "The company shows limited public AI readiness, so gap framing should remain exploratory."
    )

    return (
        f"Compared with peers such as {peer_text}, {company_name} lacks public signals for "
        f"{gap_text}; the target is {percentile_text}. {readiness_text}"
    )


def build_competitor_gap_brief(
    company_name: str,
    ai_profile: AIMaturityProfile,
) -> CompetitorGapBrief:
    record = _find_competitor_record(company_name)

    peer_group = _string_list(record.get("peer_group"))
    top_quartile_practices = _string_list(record.get("top_quartile_practices"))
    observed_practices = _string_list(record.get("observed_practices"))

    peers_raw = _as_list(record.get("competitors"))
    peer_scores = [
        _score_peer_ai_maturity(peer)
        for peer in peers_raw
        if isinstance(peer, dict)
    ]

    # If the data file only has peer names, use optional peer_ai_scores fallback.
    if not peer_scores:
        peer_scores = [
            max(0, min(3, int(score)))
            for score in _as_list(record.get("peer_ai_scores"))
            if isinstance(score, int | float)
        ]

    missing_practices = _compute_missing_practices(
        top_quartile_practices=top_quartile_practices,
        observed_practices=observed_practices,
    )

    target_score = _score_target_ai_maturity(ai_profile)
    distribution_percentile = _compute_distribution_percentile(
        target_score=target_score,
        peer_scores=peer_scores,
    )

    sparse_sector_warning = None
    if len(peer_group) < 5:
        sparse_sector_warning = (
            f"Only {len(peer_group)} competitors available; challenge expects 5–10. "
            "Treat gap findings as directional."
        )

    practice_evidence = _extract_practice_evidence(
        missing_practices=missing_practices,
        record=record,
    )

    base_confidence = 0.5

    if 5 <= len(peer_group) <= 10:
        base_confidence += 0.15
    elif len(peer_group) >= 3:
        base_confidence += 0.05

    if len(top_quartile_practices) >= 2:
        base_confidence += 0.1

    if peer_scores:
        base_confidence += 0.1

    if practice_evidence:
        base_confidence += 0.05

    if ai_profile.confidence >= 0.75:
        base_confidence += 0.05

    if sparse_sector_warning:
        base_confidence -= 0.1

    confidence = min(max(round(base_confidence, 2), 0.0), 0.9)

    summary = _build_summary(
        company_name=company_name,
        peer_group=peer_group,
        missing_practices=missing_practices,
        ai_profile=ai_profile,
        distribution_percentile=distribution_percentile,
        sparse_sector_warning=sparse_sector_warning,
    )

    return CompetitorGapBrief(
        peer_group=peer_group,
        top_quartile_practices=top_quartile_practices,
        missing_practices=missing_practices[:3],
        confidence=confidence,
        summary=summary,
        sector=record.get("sector"),
        company_size_band=record.get("company_size_band"),
        observed_practices=observed_practices,
        distribution_percentile=distribution_percentile,
        practice_evidence=practice_evidence,
        sparse_sector_warning=sparse_sector_warning,
    )
