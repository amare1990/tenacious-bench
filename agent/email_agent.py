from __future__ import annotations

from integrations.llm_client import LLMClientError, call_openrouter_json, is_llm_reply_analysis_enabled


def _signal_confidence(signals, key: str) -> float:
    try:
        return float(signals.confidence_by_signal.get(key, 0.0) or 0.0)
    except Exception:
        return 0.0


def _build_opening(company, signals, tone_mode: str) -> str:
    funding_conf = _signal_confidence(signals, 'funding')
    hiring_conf = _signal_confidence(signals, 'hiring_velocity')
    if tone_mode == 'direct' and signals.funding_signal and funding_conf >= 0.65:
        return f"I noticed {company.company_name} {str(signals.funding_signal).rstrip('.').lower()}."
    if signals.hiring_velocity_signal and hiring_conf >= 0.65:
        return f"I noticed public hiring signals around {company.company_name}, but I am treating them as directional rather than definitive."
    if signals.hiring_velocity_signal:
        return f"I saw a few public signals around {company.company_name} that may be worth checking, though I would not want to overstate them."
    return f"I came across {company.company_name} while looking at companies in this space."


def _build_gap_line(company, gap, claim_strength: str) -> str:
    if not gap.missing_practices:
        return f"{company.company_name} already shows several public operating signals that look strong relative to the peer sample."
    joined = ', '.join(gap.missing_practices[:2])
    if float(getattr(gap, 'confidence', 0.0) or 0.0) < 0.65:
        return f"The peer comparison is low-confidence, but it raised a question for me around {joined}."
    if claim_strength == 'moderate':
        return f"Compared with the peer sample, there may be a gap around {joined}."
    return f"Compared with the peer sample, I wondered whether {joined} might be worth examining."


def _build_cta(tone_mode: str) -> str:
    if tone_mode == 'direct':
        return 'Would a 30-minute conversation next week be useful?'
    if tone_mode == 'balanced':
        return 'Would it be useful to compare notes for 30 minutes?'
    return 'If relevant, I would be glad to share a few observations and compare notes.'


def _generate_email_fallback(company, signals, ai, gap, segment_result, policy_result):
    subject = f"{company.company_name} - quick observation"
    body = '\n'.join([
        'Hi,',
        '',
        _build_opening(company, signals, policy_result['tone_mode']),
        '',
        f"Working angle: {segment_result['segment']}. Public AI-readiness estimate: {ai.score}/3, confidence {round(float(ai.confidence), 2)}.",
        '',
        _build_gap_line(company, gap, policy_result['claim_strength']),
        '',
        _build_cta(policy_result['tone_mode']),
        '',
        'Best,',
        'Tenacious',
    ])
    return {'subject': subject, 'body': body, 'source': 'fallback'}


def _llm_enabled() -> bool:
    return is_llm_reply_analysis_enabled()


def _generate_email_with_llm(company, signals, ai, gap, segment_result, policy_result):
    system_prompt = (
        'You are drafting a concise B2B outbound email for Tenacious Consulting. '
        'Return JSON with keys subject and body only. Use only the supplied evidence. '
        'Stay restrained, research-grounded, and avoid overclaiming.'
    )
    user_prompt = f"""
Company: {company.company_name}
Industry: {company.industry}
Location: {company.location}
Funding stage: {company.funding_stage}
Signals summary: {signals.summary}
AI score: {ai.score} / 3
AI rationale: {ai.rationale}
Missing practices: {gap.missing_practices}
Segment: {segment_result['segment']}
Segment rationale: {segment_result['rationale']}
Tone mode: {policy_result['tone_mode']}
Claim strength: {policy_result['claim_strength']}
""".strip()
    data = call_openrouter_json(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.2)
    subject = str(data.get('subject', '')).strip()
    body = str(data.get('body', '')).strip()
    if not subject or not body:
        raise LLMClientError('LLM email drafting returned empty subject or body')
    return {'subject': subject, 'body': body, 'source': 'llm'}


def generate_email(company, signals, ai, gap, segment_result, policy_result):
    if _llm_enabled():
        try:
            return _generate_email_with_llm(company, signals, ai, gap, segment_result, policy_result)
        except (LLMClientError, ValueError):
            pass
    return _generate_email_fallback(company, signals, ai, gap, segment_result, policy_result)


def generate_followup_email(company_name: str, analysis) -> dict:
    if analysis.reply_type == 'interested':
        return {
            'subject': f'Re: {company_name} - next step',
            'body': 'Hi,\n\nGlad to hear that. I would be happy to coordinate a 30-minute conversation and send over a few time options.\n\nBest,\nTenacious',
            'source': 'fallback',
        }
    if analysis.reply_type == 'information_request':
        return {
            'subject': f'Re: {company_name} - more context',
            'body': 'Hi,\n\nAbsolutely. We typically help teams that are scaling engineering capacity, filling specialized AI, data, or infra gaps, or trying to move faster without overloading internal recruiting.\n\nIf useful, I can also summarize the specific observation that made me reach out.\n\nBest,\nTenacious',
            'source': 'fallback',
        }
    if analysis.reply_type == 'defer':
        return {
            'subject': f'Re: {company_name} - happy to follow up later',
            'body': 'Hi,\n\nUnderstood. Happy to circle back at a better time.\n\nBest,\nTenacious',
            'source': 'fallback',
        }
    if analysis.reply_type == 'unclear':
        return {
            'subject': f'Re: {company_name}',
            'body': 'Hi,\n\nThanks for the reply. Happy to clarify or share a bit more context if helpful.\n\nBest,\nTenacious',
            'source': 'fallback',
        }
    return {
        'subject': f'Re: {company_name}',
        'body': 'Understood. Thanks for the reply.',
        'source': 'fallback',
    }
