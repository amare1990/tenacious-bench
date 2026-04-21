from __future__ import annotations

from briefs.models import BenchMatchSummary


def decide_outreach_policy(
    segment_result: dict,
    bench: BenchMatchSummary,
) -> dict:
    segment = segment_result["segment"]
    confidence = float(segment_result["confidence"])

    should_contact = True
    tone_mode = "exploratory"
    claim_strength = "soft"
    require_handoff = False
    allow_capacity_language = False
    reason_parts: list[str] = []

    if confidence >= 0.8:
        tone_mode = "direct"
        claim_strength = "moderate"
        reason_parts.append("Signal confidence is high enough for a direct outreach style.")
    elif confidence >= 0.6:
        tone_mode = "balanced"
        claim_strength = "soft"
        reason_parts.append("Signal confidence supports outreach, but claims should remain measured.")
    else:
        tone_mode = "exploratory"
        claim_strength = "soft"
        reason_parts.append("Signal confidence is limited; outreach should avoid strong assumptions.")

    if segment.startswith("Exploratory"):
        tone_mode = "exploratory"
        claim_strength = "soft"
        reason_parts.append("Segment fit is weak, so the system should ask rather than assert.")

    if not bench.fit:
        allow_capacity_language = False
        require_handoff = True
        reason_parts.append("Bench match is weak; the system must avoid explicit staffing commitments.")
    else:
        allow_capacity_language = True
        reason_parts.append("Bench fit is strong enough to discuss capability directionally.")

    if confidence < 0.35:
        should_contact = False
        reason_parts.append("Overall confidence is too low to justify outreach.")

    return {
        "should_contact": should_contact,
        "tone_mode": tone_mode,
        "claim_strength": claim_strength,
        "require_handoff": require_handoff,
        "allow_capacity_language": allow_capacity_language,
        "reason": " ".join(reason_parts),
    }
