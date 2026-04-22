"""Hiring-signal enrichment.

Builds a structured HiringSignalBrief by combining local fixture signals with any
raw snapshots available under data/raw/.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from briefs.models import HiringSignalBrief
from enrichment.crunchbase import find_company_profile
from enrichment.layoffs import build_layoff_signal
from enrichment.source_inventory import RAW_DIR, json_load, slugify_company_name


FIXTURE_SIGNAL_PATH = Path(__file__).resolve().parent.parent / "data" / "company_signals.json"
RAW_JOB_POSTS_DIR = RAW_DIR / "job_posts"
RAW_TECH_STACK_DIR = RAW_DIR / "tech_stack"
RAW_PRESS_DIR = RAW_DIR / "press"


def get_job_post_velocity_mock(company_name: str) -> dict:
    return {
        "open_roles": 8,
        "role_change_60d": 2.5,
        "evidence": [f"8 public engineering roles found for {company_name}"],
    }


def _normalize_name(name: str) -> str:
    return " ".join(name.strip().lower().split())


def _load_signal_records() -> list[dict[str, Any]]:
    data = json_load(FIXTURE_SIGNAL_PATH, [])
    if not isinstance(data, list):
        raise ValueError("company_signals.json must contain a list of signal records.")
    return data


def _find_fixture_signal_record(company_name: str) -> dict[str, Any] | None:
    normalized_query = _normalize_name(company_name)
    for record in _load_signal_records():
        record_name = record.get("company_name", "")
        if _normalize_name(record_name) == normalized_query:
            return record
    return None


def _load_company_specific_json(directory: Path, company_name: str) -> dict[str, Any] | list[Any] | None:
    slug = slugify_company_name(company_name)
    candidate = directory / f"{slug}.json"
    if candidate.exists() and candidate.stat().st_size > 0:
        return json_load(candidate, None)
    return None


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    text = text.replace("Z", "+00:00")
    formats = [None, "%Y-%m-%d", "%Y-%m", "%Y-%m-%d %H:%M:%S.%f"]
    for fmt in formats:
        try:
            if fmt is None:
                return datetime.fromisoformat(text)
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _build_funding_signal(company_name: str) -> tuple[str | None, dict[str, Any], float]:
    try:
        company = find_company_profile(company_name)
    except ValueError:
        return None, {}, 0.0

    details = {
        "funding_stage": company.funding_stage,
        "last_funding_date": company.last_funding_date,
        "source": company.source,
    }

    if not company.last_funding_date and not company.funding_stage:
        return None, details, 0.0

    confidence = 0.45
    last_funding_dt = _parse_datetime(str(company.last_funding_date)) if company.last_funding_date else None
    if company.funding_stage:
        confidence += 0.15
    if last_funding_dt:
        age_days = (datetime.now(timezone.utc) - last_funding_dt.astimezone(timezone.utc)).days
        details["age_days"] = age_days
        if age_days <= 180:
            confidence += 0.25
            text = f"Closed {company.funding_stage or 'a funding round'} within the last 180 days."
            return text, details, round(min(confidence, 0.9), 2)
        text = f"Funding history shows {company.funding_stage or 'a round'}; last public funding appears older than 180 days."
        return text, details, round(min(confidence, 0.75), 2)

    text = f"Public data shows funding stage {company.funding_stage}."
    return text, details, round(min(confidence, 0.65), 2)


def _build_hiring_velocity_signal(company_name: str, fixture_record: dict[str, Any] | None) -> tuple[str | None, dict[str, Any], float]:
    payload = _load_company_specific_json(RAW_JOB_POSTS_DIR, company_name)
    if payload is None:
        if fixture_record and fixture_record.get("hiring_velocity_signal"):
            return (
                str(fixture_record.get("hiring_velocity_signal")),
                {"source": "fixture", "source_path": str(FIXTURE_SIGNAL_PATH.relative_to(Path(__file__).resolve().parent.parent))},
                float((fixture_record.get("confidence_by_signal") or {}).get("hiring_velocity", 0.55)),
            )
        return None, {}, 0.0

    details: dict[str, Any] = {"source": "raw_job_posts", "source_path": str((RAW_JOB_POSTS_DIR / f'{slugify_company_name(company_name)}.json').relative_to(Path(__file__).resolve().parent.parent))}
    open_roles = 0
    role_change_60d = None
    titles: list[str] = []

    if isinstance(payload, dict):
        open_roles = int(payload.get("open_roles", 0) or 0)
        role_change_60d = payload.get("role_change_60d")
        titles = [str(title) for title in payload.get("titles", []) if title]
        details.update({k: v for k, v in payload.items() if k not in {"titles"}})
    elif isinstance(payload, list):
        open_roles = len(payload)
        titles = [str(item.get("title")) for item in payload if isinstance(item, dict) and item.get("title")]
        details["sample_titles"] = titles[:10]

    if open_roles <= 0:
        return None, details, 0.0

    confidence = 0.65 if role_change_60d is None else 0.78
    title_snippet = ", ".join(titles[:3]) if titles else f"{open_roles} open roles"
    if role_change_60d not in (None, ""):
        signal = f"{open_roles} public engineering-adjacent roles found; 60-day hiring velocity multiplier {role_change_60d}."
    else:
        signal = f"{open_roles} public engineering-adjacent roles found ({title_snippet})."

    details["open_roles"] = open_roles
    details["role_change_60d"] = role_change_60d
    details["titles"] = titles[:20]
    return signal, details, round(min(confidence, 0.9), 2)


def _build_leadership_signal(company_name: str, fixture_record: dict[str, Any] | None) -> tuple[str | None, dict[str, Any], float]:
    payload = _load_company_specific_json(RAW_PRESS_DIR, company_name)
    leadership_keywords = ("cto", "vp engineering", "vice president engineering", "head of engineering")
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)

    if isinstance(payload, list):
        for item in payload:
            if not isinstance(item, dict):
                continue
            text = " ".join(str(item.get(key, "")) for key in ["title", "headline", "summary"]).lower()
            published_at = _parse_datetime(str(item.get("published_at") or item.get("date") or ""))
            if any(keyword in text for keyword in leadership_keywords) and (published_at is None or published_at >= cutoff):
                summary = str(item.get("title") or item.get("headline") or "Leadership change observed")
                details = dict(item)
                details["source"] = "raw_press"
                details["source_path"] = str((RAW_PRESS_DIR / f'{slugify_company_name(company_name)}.json').relative_to(Path(__file__).resolve().parent.parent))
                return summary, details, 0.8 if published_at else 0.65

    if fixture_record and fixture_record.get("leadership_change_signal"):
        return (
            str(fixture_record.get("leadership_change_signal")),
            {"source": "fixture", "source_path": str(FIXTURE_SIGNAL_PATH.relative_to(Path(__file__).resolve().parent.parent))},
            float((fixture_record.get("confidence_by_signal") or {}).get("leadership_change", 0.55)),
        )

    return None, {}, 0.0


def _build_tech_stack_signal(company_name: str, fixture_record: dict[str, Any] | None) -> tuple[str | None, dict[str, Any], float]:
    payload = _load_company_specific_json(RAW_TECH_STACK_DIR, company_name)
    if payload is None:
        if fixture_record and fixture_record.get("tech_stack_signal"):
            return (
                str(fixture_record.get("tech_stack_signal")),
                {"source": "fixture", "source_path": str(FIXTURE_SIGNAL_PATH.relative_to(Path(__file__).resolve().parent.parent))},
                float((fixture_record.get("confidence_by_signal") or {}).get("tech_stack", 0.5)),
            )
        return None, {}, 0.0

    technologies: list[str] = []
    details: dict[str, Any] = {"source": "raw_tech_stack", "source_path": str((RAW_TECH_STACK_DIR / f'{slugify_company_name(company_name)}.json').relative_to(Path(__file__).resolve().parent.parent))}

    if isinstance(payload, dict):
        for key in ["technologies", "stack", "tools"]:
            value = payload.get(key)
            if isinstance(value, list):
                technologies.extend(str(item) for item in value if item)
        details.update({k: v for k, v in payload.items() if k not in {"technologies", "stack", "tools"}})
    elif isinstance(payload, list):
        technologies.extend(str(item) for item in payload if item)

    technologies = list(dict.fromkeys(technologies))
    if not technologies:
        return None, details, 0.0

    snippet = ", ".join(technologies[:5])
    signal = f"Observed public stack signals: {snippet}."
    details["technologies"] = technologies
    confidence = 0.72 if len(technologies) >= 3 else 0.6
    return signal, details, confidence


def _build_summary(signals: list[str]) -> str:
    cleaned = [signal.strip() for signal in signals if signal and signal.strip()]
    if not cleaned:
        return "No strong public hiring or operating signals were found."
    return "; ".join(cleaned)


def build_hiring_signal_brief(company_name: str) -> HiringSignalBrief:
    fixture_record = _find_fixture_signal_record(company_name)

    funding_signal, funding_details, funding_conf = _build_funding_signal(company_name)
    hiring_signal, hiring_details, hiring_conf = _build_hiring_velocity_signal(company_name, fixture_record)
    layoffs_signal, layoffs_details, layoffs_conf = build_layoff_signal(company_name)
    leadership_signal, leadership_details, leadership_conf = _build_leadership_signal(company_name, fixture_record)
    tech_stack_signal, tech_stack_details, tech_stack_conf = _build_tech_stack_signal(company_name, fixture_record)

    confidence_by_signal = {
        "funding": float(funding_conf),
        "hiring_velocity": float(hiring_conf),
        "layoffs": float(layoffs_conf),
        "leadership_change": float(leadership_conf),
        "tech_stack": float(tech_stack_conf),
    }

    source_paths = sorted(
        {
            path
            for path in [
                funding_details.get("source_path"),
                hiring_details.get("source_path"),
                layoffs_details.get("source_path"),
                leadership_details.get("source_path"),
                tech_stack_details.get("source_path"),
            ]
            if path
        }
    )

    missing_inputs: list[str] = []
    if not hiring_signal:
        missing_inputs.append("job_posts_snapshot")
    if not leadership_signal:
        missing_inputs.append("press_snapshot")
    if not tech_stack_signal:
        missing_inputs.append("tech_stack_snapshot")

    return HiringSignalBrief(
        funding_signal=funding_signal,
        hiring_velocity_signal=hiring_signal,
        layoffs_signal=layoffs_signal,
        leadership_change_signal=leadership_signal,
        tech_stack_signal=tech_stack_signal,
        confidence_by_signal=confidence_by_signal,
        overall_summary=_build_summary([
            funding_signal or "",
            hiring_signal or "",
            layoffs_signal or "",
            leadership_signal or "",
            tech_stack_signal or "",
        ]),
        funding_details=funding_details,
        hiring_velocity_details=hiring_details,
        layoffs_details=layoffs_details,
        leadership_change_details=leadership_details,
        tech_stack_details=tech_stack_details,
        source_paths=source_paths,
        missing_inputs=missing_inputs,
    )
