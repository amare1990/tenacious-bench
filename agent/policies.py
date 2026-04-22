from __future__ import annotations

from typing import Dict

from briefs.models import BenchMatchSummary


def apply_policies(classification: Dict, ai_profile: Dict) -> Dict:
    """Return policy decisions: whether to soften language, bench gating, and handoff."""
    segment = classification.get("segment", "")
    confidence = classification.get("confidence", 0.0)

    soften = confidence < 0.6 or ai_profile.get("confidence", 0.0) < 0.5
    bench_commit = False  # by default do not commit staffing in initial email
    handoff = False

    return {"soften": soften, "bench_commit": bench_commit, "handoff": handoff}


def decide_outreach_policy(
    segment_result: dict,
    bench: BenchMatchSummary,
    ai_confidence: float | None = None,
) -> dict:
    segment = segment_result["segment"]
    confidence = float(segment_result["confidence"])
    ai_confidence = 0.0 if ai_confidence is None else float(ai_confidence)

    effective_confidence = min(confidence, ai_confidence) if ai_confidence > 0 else confidence

    should_contact = True
    tone_mode = "exploratory"
    claim_strength = "soft"
    require_handoff = False
    allow_capacity_language = False
    reason_parts: list[str] = []

    if effective_confidence >= 0.8:
        tone_mode = "direct"
        claim_strength = "moderate"
        reason_parts.append("Segment and AI-confidence signals support direct outreach.")
    elif effective_confidence >= 0.6:
        tone_mode = "balanced"
        claim_strength = "soft"
        reason_parts.append("Signals support outreach, but claims should remain measured.")
    else:
        tone_mode = "exploratory"
        claim_strength = "soft"
        reason_parts.append("Confidence is limited, so outreach should ask rather than assert.")

    if segment.startswith("Exploratory"):
        tone_mode = "exploratory"
        claim_strength = "soft"
        reason_parts.append("Segment fit is weak, so the system should avoid strong assumptions.")

    if not bench.fit:
        allow_capacity_language = False
        require_handoff = True
        reason_parts.append("Bench match is weak; avoid explicit staffing commitments.")
    else:
        allow_capacity_language = True
        reason_parts.append("Bench fit is strong enough to discuss capability directionally.")

    if effective_confidence < 0.35:
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
