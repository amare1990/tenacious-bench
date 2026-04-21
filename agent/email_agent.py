from __future__ import annotations

from integrations.llm_client import (
    call_openrouter_json,
    is_llm_reply_analysis_enabled,
    LLMClientError,
)


def _build_opening(company, signals, tone_mode: str) -> str:
    if tone_mode == "direct" and signals.funding_signal:
        return f"I noticed that {company.company_name} {signals.funding_signal.lower()}."
    if signals.hiring_velocity_signal:
        return f"I noticed {company.company_name} appears to be hiring actively."
    return f"I came across {company.company_name} while looking at companies in this space."


def _build_gap_line(company, gap, claim_strength: str) -> str:
    if not gap.missing_practices:
        return (
            f"It looks like {company.company_name} is already showing several strong "
            f"public operating signals relative to peers."
        )

    joined = ", ".join(gap.missing_practices[:2])

    if claim_strength == "moderate":
        return (
            f"Compared with peers in the same space, it looks like there may be a gap "
            f"around {joined}."
        )
    return (
        f"Compared with peers in the same space, I wondered whether {joined} "
        f"might be an area worth examining."
    )


def _build_cta(tone_mode: str) -> str:
    if tone_mode == "direct":
        return "Would a 30-minute conversation next week be useful?"
    if tone_mode == "balanced":
        return "Would it be useful to compare notes for 30 minutes?"
    return "If relevant, I’d be glad to share a few observations and compare notes."


def _generate_email_fallback(company, signals, ai, gap, segment_result, policy_result):
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
        "source": "fallback",
    }


def _llm_enabled() -> bool:
    # Reuse the same enablement pattern as reply analysis for now
    return is_llm_reply_analysis_enabled()


def _generate_email_with_llm(company, signals, ai, gap, segment_result, policy_result):
    system_prompt = """
You are drafting a B2B outbound sales email for Tenacious Consulting.

Return ONLY a JSON object with exactly these keys:
- subject
- body

Requirements:
- The email must sound professional, restrained, and research-grounded.
- Do not fabricate facts.
- Use only the evidence provided.
- Do not overclaim certainty when confidence is limited.
- Keep the email concise.
- Ask for a short discovery conversation.
- Email is primary; do not mention SMS.
- Avoid sounding spammy or overly promotional.
- Do not say "offshore" unless explicitly provided.
- Preserve the claim strength and tone mode constraints.
""".strip()

    user_prompt = f"""
Company:
- name: {company.company_name}
- industry: {company.industry}
- location: {company.location}
- funding_stage: {company.funding_stage}
- last_funding_date: {company.last_funding_date}

Hiring signals:
- funding_signal: {signals.funding_signal}
- hiring_velocity_signal: {signals.hiring_velocity_signal}
- layoffs_signal: {signals.layoffs_signal}
- leadership_change_signal: {signals.leadership_change_signal}
- tech_stack_signal: {signals.tech_stack_signal}
- summary: {signals.summary}

AI maturity:
- score: {ai.score}
- confidence: {ai.confidence}
- rationale: {ai.rationale}

Competitor gap:
- peer_group: {gap.peer_group}
- missing_practices: {gap.missing_practices}
- summary: {gap.summary}

Segmentation:
- segment: {segment_result["segment"]}
- confidence: {segment_result["confidence"]}
- rationale: {segment_result["rationale"]}

Policy:
- tone_mode: {policy_result["tone_mode"]}
- claim_strength: {policy_result["claim_strength"]}
- should_contact: {policy_result["should_contact"]}
- allow_capacity_language: {policy_result["allow_capacity_language"]}

Draft a short outbound email.
""".strip()

    data = call_openrouter_json(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.2,
    )

    subject = str(data.get("subject", "")).strip()
    body = str(data.get("body", "")).strip()

    if not subject or not body:
        raise LLMClientError("LLM email drafting returned empty subject or body")

    return {
        "subject": subject,
        "body": body,
        "source": "llm",
    }


def generate_email(company, signals, ai, gap, segment_result, policy_result):
    if _llm_enabled():
        try:
            return _generate_email_with_llm(
                company=company,
                signals=signals,
                ai=ai,
                gap=gap,
                segment_result=segment_result,
                policy_result=policy_result,
            )
        except LLMClientError:
            pass
        except ValueError:
            pass

    return _generate_email_fallback(
        company=company,
        signals=signals,
        ai=ai,
        gap=gap,
        segment_result=segment_result,
        policy_result=policy_result,
    )


def generate_followup_email(company_name: str, analysis) -> dict:
    if analysis.reply_type == "interested":
        return {
            "subject": f"Re: {company_name} – next step",
            "body": """
Hi,

Glad to hear that. I’d be happy to coordinate a 30-minute conversation and send over a few time options.

Best,
Tenacious
""".strip(),
            "source": "fallback",
        }

    if analysis.reply_type == "information_request":
        return {
            "subject": f"Re: {company_name} – more context",
            "body": """
Hi,

Absolutely. We typically help teams that are scaling engineering capacity, filling specialized AI/data/infra gaps, or trying to move faster without overloading internal recruiting.

If useful, I can also summarize the specific observation that made me reach out.

Best,
Tenacious
""".strip(),
            "source": "fallback",
        }

    if analysis.reply_type == "defer":
        return {
            "subject": f"Re: {company_name} – happy to follow up later",
            "body": """
Hi,

Understood. Happy to circle back at a better time.

Best,
Tenacious
""".strip(),
            "source": "fallback",
        }

    if analysis.reply_type == "unclear":
        return {
            "subject": f"Re: {company_name}",
            "body": """
Hi,

Thanks for the reply. Happy to clarify or share a bit more context if helpful.

Best,
Tenacious
""".strip(),
            "source": "fallback",
        }

    return {
        "subject": f"Re: {company_name}",
        "body": "Understood. Thanks for the reply.",
        "source": "fallback",
    }
