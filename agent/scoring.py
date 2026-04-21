from __future__ import annotations

from typing import Optional

from briefs.models import (
    CompanyProfile,
    HiringSignalBrief,
    AIMaturityProfile,
    CompetitorGapBrief,
)


def _has_text(value: Optional[str]) -> bool:
    return bool(value and value.strip())


def classify_icp_segment(
    company: CompanyProfile,
    signals: HiringSignalBrief,
    ai_profile: AIMaturityProfile,
    gap_brief: CompetitorGapBrief,
) -> dict:
    """
    Rule-based ICP classification.

    Segment priority:
    1. Recently funded
    2. Restructuring / layoffs
    3. New CTO / VP Engineering
    4. Specialized capability gap
    """

    funding_present = _has_text(signals.funding_signal)
    layoffs_present = _has_text(signals.layoffs_signal)
    leadership_present = _has_text(signals.leadership_change_signal)
    hiring_present = _has_text(signals.hiring_velocity_signal)
    gap_present = len(gap_brief.missing_practices) > 0

    funding_conf = float(signals.confidence_by_signal.get("funding", 0.0))
    layoffs_conf = float(signals.confidence_by_signal.get("layoffs", 0.0))
    leadership_conf = float(signals.confidence_by_signal.get("leadership_change", 0.0))
    hiring_conf = float(signals.confidence_by_signal.get("hiring_velocity", 0.0))
    tech_conf = float(signals.confidence_by_signal.get("tech_stack", 0.0))

    segment = "Unclassified"
    confidence = 0.4
    rationale_parts: list[str] = []

    # Segment 2: Restructuring / layoffs
    if layoffs_present and layoffs_conf >= 0.65:
        segment = "Segment 2 - Restructuring / Layoffs"
        confidence = min(0.55 + layoffs_conf * 0.4, 0.95)
        rationale_parts.append("Recent restructuring signal is present.")
        if hiring_present:
            rationale_parts.append("Selective hiring may indicate cost reshaping rather than full slowdown.")
        return {
            "segment": segment,
            "confidence": round(confidence, 2),
            "rationale": " ".join(rationale_parts),
        }

    # Segment 3: New CTO / VP Engineering
    if leadership_present and leadership_conf >= 0.65:
        segment = "Segment 3 - Engineering Leadership Transition"
        confidence = min(0.55 + leadership_conf * 0.4, 0.95)
        rationale_parts.append("Recent engineering leadership change is present.")
        if hiring_present:
            rationale_parts.append("Ongoing hiring suggests an active operating window.")
        return {
            "segment": segment,
            "confidence": round(confidence, 2),
            "rationale": " ".join(rationale_parts),
        }

    # Segment 1: Recently funded
    if funding_present and funding_conf >= 0.65:
        segment = "Segment 1 - Recently Funded"
        confidence = min(0.5 + (funding_conf * 0.25) + (hiring_conf * 0.2), 0.95)
        rationale_parts.append("Recent funding signal is present.")
        if hiring_present:
            rationale_parts.append("Hiring velocity supports a scaling narrative.")
        return {
            "segment": segment,
            "confidence": round(confidence, 2),
            "rationale": " ".join(rationale_parts),
        }

    # Segment 4: Specialized capability gap
    if ai_profile.score >= 2 and gap_present:
        segment = "Segment 4 - Specialized Capability Gap"
        confidence = min(0.45 + (ai_profile.confidence * 0.25) + (gap_brief.confidence * 0.25) + (tech_conf * 0.15), 0.95)
        rationale_parts.append("AI readiness is high enough to support a capability-gap conversation.")
        rationale_parts.append("Peer comparison suggests missing top-quartile practices.")
        return {
            "segment": segment,
            "confidence": round(confidence, 2),
            "rationale": " ".join(rationale_parts),
        }

    # Fallback exploratory state
    if hiring_present or funding_present or gap_present:
        segment = "Exploratory - Weak Signal"
        confidence = 0.5
        rationale_parts.append("Some public signal is present, but evidence is not strong enough for a narrow segment pitch.")
    else:
        segment = "Exploratory - Low Confidence"
        confidence = 0.35
        rationale_parts.append("Public evidence is too weak for a segment-specific outreach angle.")

    return {
        "segment": segment,
        "confidence": round(confidence, 2),
        "rationale": " ".join(rationale_parts),
    }
