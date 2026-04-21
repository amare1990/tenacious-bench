from __future__ import annotations


def _build_opening(company, signals, tone_mode: str) -> str:
    if tone_mode == "direct" and signals.funding_signal:
        return f"I noticed that {company.company_name} {signals.funding_signal.lower()}."
    if signals.hiring_velocity_signal:
        return f"I noticed {company.company_name} appears to be hiring actively."
    return f"I came across {company.company_name} while looking at companies in this space."


def _build_gap_line(company, gap, claim_strength: str) -> str:
    if not gap.missing_practices:
        return f"It looks like {company.company_name} is already showing several strong public operating signals relative to peers."

    joined = ", ".join(gap.missing_practices[:2])

    if claim_strength == "moderate":
        return f"Compared with peers in the same space, it looks like there may be a gap around {joined}."
    return f"Compared with peers in the same space, I wondered whether {joined} might be an area worth examining."


def _build_cta(tone_mode: str) -> str:
    if tone_mode == "direct":
        return "Would a 30-minute conversation next week be useful?"
    if tone_mode == "balanced":
        return "Would it be useful to compare notes for 30 minutes?"
    return "If relevant, I’d be glad to share a few observations and compare notes."


def generate_email(company, signals, ai, gap, segment_result, policy_result):
    subject = f"{company.company_name} – quick observation"

    opening = _build_opening(company, signals, policy_result["tone_mode"])
    gap_line = _build_gap_line(company, gap, policy_result["claim_strength"])
    cta = _build_cta(policy_result["tone_mode"])

    segment_context = f"Working angle: {segment_result['segment']}."
    ai_context = f"Public AI readiness appears to be {ai.score}/3."

    body = f"""
Hi,

{opening}

{segment_context} {ai_context}

{gap_line}

{cta}

Best,
Tenacious
""".strip()

    return {
        "subject": subject,
        "body": body,
    }
