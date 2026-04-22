from __future__ import annotations

from briefs.models import AIMaturityProfile, CompanyProfile, CompetitorGapBrief, HiringSignalBrief


def _has_text(value: object) -> bool:
    return bool(value and str(value).strip())


def classify_icp_segment(
    company: CompanyProfile,
    signals: HiringSignalBrief,
    ai_profile: AIMaturityProfile,
    gap_brief: CompetitorGapBrief,
) -> dict:
    funding_conf = float(signals.confidence_by_signal.get('funding', 0.0))
    layoffs_conf = float(signals.confidence_by_signal.get('layoffs', 0.0))
    leadership_conf = float(signals.confidence_by_signal.get('leadership_change', 0.0))
    hiring_conf = float(signals.confidence_by_signal.get('hiring_velocity', 0.0))
    tech_conf = float(signals.confidence_by_signal.get('tech_stack', 0.0))

    funding_present = _has_text(signals.funding_signal)
    layoffs_present = _has_text(signals.layoffs_signal)
    leadership_present = _has_text(signals.leadership_change_signal)
    hiring_present = _has_text(signals.hiring_velocity_signal)
    gap_present = bool(gap_brief.missing_practices)

    if layoffs_present and layoffs_conf >= 0.65:
        confidence = min(0.55 + layoffs_conf * 0.35 + tech_conf * 0.1, 0.95)
        return {
            'segment': 'Segment 2 - Mid-market Restructuring',
            'confidence': round(confidence, 2),
            'rationale': 'Recent layoff/restructuring signal is present and confidence is strong.',
        }

    if leadership_present and leadership_conf >= 0.65:
        confidence = min(0.55 + leadership_conf * 0.35 + hiring_conf * 0.1, 0.95)
        return {
            'segment': 'Segment 3 - Engineering Leadership Transition',
            'confidence': round(confidence, 2),
            'rationale': 'Recent CTO/VP Engineering change creates a plausible vendor reassessment window.',
        }

    if funding_present and funding_conf >= 0.65:
        confidence = min(0.5 + funding_conf * 0.25 + hiring_conf * 0.2 + tech_conf * 0.1, 0.95)
        return {
            'segment': 'Segment 1 - Recently Funded',
            'confidence': round(confidence, 2),
            'rationale': 'Funding and hiring signals support a scaling narrative.',
        }

    if ai_profile.score >= 2 and gap_present:
        confidence = min(0.45 + ai_profile.confidence * 0.25 + gap_brief.confidence * 0.2 + tech_conf * 0.1, 0.95)
        return {
            'segment': 'Segment 4 - Specialized Capability Gap',
            'confidence': round(confidence, 2),
            'rationale': 'AI readiness and competitor-gap evidence support a capability-gap conversation.',
        }

    if funding_present or hiring_present or gap_present:
        return {
            'segment': 'Exploratory - Weak Signal',
            'confidence': 0.5,
            'rationale': 'Some public evidence exists, but not enough for a narrow pitch.',
        }

    return {
        'segment': 'Exploratory - Low Confidence',
        'confidence': 0.35,
        'rationale': 'Public evidence is too weak for segment-specific outreach.',
    }
