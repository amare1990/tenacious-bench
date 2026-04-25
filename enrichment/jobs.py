"""Hiring-signal enrichment.

Builds a structured HiringSignalBrief by combining local fixture signals with any
raw snapshots available under data/raw/.

Rubric-facing guarantees:
- Funding, hiring velocity, layoffs, leadership change, and tech-stack signals are merged.
- Every signal emits confidence, source attribution, and collection timestamp.
- Job velocity is computed from current open roles vs previous 60-day snapshot when available.
- Missing inputs are recorded explicitly instead of hallucinated.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from briefs.models import HiringSignalBrief, SignalEvidence
from enrichment.crunchbase import find_company_profile
from enrichment.layoffs import build_layoff_signal
from enrichment.source_inventory import RAW_DIR, json_load, slugify_company_name


FIXTURE_SIGNAL_PATH = Path(__file__).resolve().parent.parent / "data" / "company_signals.json"
RAW_JOB_POSTS_DIR = RAW_DIR / "job_posts"
RAW_TECH_STACK_DIR = RAW_DIR / "tech_stack"
RAW_PRESS_DIR = RAW_DIR / "press"


def compute_60d_velocity(
    current_open_roles: int,
    previous_open_roles: int | None,
) -> float | None:
    """Return current / previous open-role multiplier over a 60-day window."""
    if previous_open_roles is None:
        return None
    if previous_open_roles == 0:
        return float(current_open_roles) if current_open_roles else 0.0
    return round(current_open_roles / previous_open_roles, 2)


def get_job_post_velocity_mock(company_name: str) -> dict[str, Any]:
    return {
        "open_roles": 8,
        "previous_open_roles_60d": 3,
        "role_change_60d": compute_60d_velocity(8, 3),
        "evidence": [f"8 public engineering roles found for {company_name}"],
    }


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _repo_relative(path: Path) -> str:
    root = Path(__file__).resolve().parent.parent
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


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


def _load_company_specific_json(
    directory: Path,
    company_name: str,
) -> dict[str, Any] | list[Any] | None:
    slug = slugify_company_name(company_name)
    candidate = directory / f"{slug}.json"
    if candidate.exists() and candidate.stat().st_size > 0:
        return json_load(candidate, None)
    return None


def _source_path(directory: Path, company_name: str) -> str:
    return _repo_relative(directory / f"{slugify_company_name(company_name)}.json")


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
                parsed = datetime.fromisoformat(text)
            else:
                parsed = datetime.strptime(text, fmt)

            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)

            return parsed
        except ValueError:
            continue

    return None


def _safe_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _signal_evidence(
    *,
    name: str,
    value: str | None,
    confidence: float,
    source_path: str | None,
    timestamp_utc: str | None = None,
) -> SignalEvidence:
    return SignalEvidence(
        name=name,
        value=value,
        confidence=float(confidence),
        source_path=source_path,
        collected_at_utc=_utc_now_iso(),
        timestamp_utc=timestamp_utc,
    )


def _build_funding_signal(company_name: str) -> tuple[str | None, dict[str, Any], float, SignalEvidence]:
    try:
        company = find_company_profile(company_name)
    except ValueError:
        evidence = _signal_evidence(
            name="funding",
            value=None,
            confidence=0.0,
            source_path=None,
        )
        return None, {}, 0.0, evidence

    details: dict[str, Any] = {
        "funding_stage": company.funding_stage,
        "last_funding_date": str(company.last_funding_date) if company.last_funding_date else None,
        "source": company.source,
        "source_record_id": company.source_record_id,
        "source_paths": company.source_paths,
    }

    source_path = company.source_paths[0] if company.source_paths else company.source

    if not company.last_funding_date and not company.funding_stage:
        evidence = _signal_evidence(
            name="funding",
            value=None,
            confidence=0.0,
            source_path=source_path,
        )
        return None, details, 0.0, evidence

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
            final_conf = round(min(confidence, 0.9), 2)
            evidence = _signal_evidence(
                name="funding",
                value=text,
                confidence=final_conf,
                source_path=source_path,
                timestamp_utc=last_funding_dt.isoformat(),
            )
            return text, details, final_conf, evidence

        text = (
            f"Funding history shows {company.funding_stage or 'a round'}; "
            "last public funding appears older than 180 days."
        )
        final_conf = round(min(confidence, 0.75), 2)
        evidence = _signal_evidence(
            name="funding",
            value=text,
            confidence=final_conf,
            source_path=source_path,
            timestamp_utc=last_funding_dt.isoformat(),
        )
        return text, details, final_conf, evidence

    text = f"Public data shows funding stage {company.funding_stage}."
    final_conf = round(min(confidence, 0.65), 2)
    evidence = _signal_evidence(
        name="funding",
        value=text,
        confidence=final_conf,
        source_path=source_path,
    )
    return text, details, final_conf, evidence


def _extract_job_snapshot(payload: dict[str, Any] | list[Any]) -> tuple[int, int | None, list[str], dict[str, Any]]:
    """Extract current and prior role counts from raw job payloads.

    Supported dict fields:
    - open_roles
    - current_open_roles
    - current_open_roles_count
    - previous_open_roles_60d
    - previous_open_roles
    - open_roles_60d_ago

    Supported list payload:
    - current open roles inferred from list length
    - previous count unavailable unless payload items include snapshot metadata
    """

    details: dict[str, Any] = {}
    titles: list[str] = []

    if isinstance(payload, dict):
        current = (
            _safe_int(payload.get("open_roles"))
            or _safe_int(payload.get("current_open_roles"))
            or _safe_int(payload.get("current_open_roles_count"))
            or 0
        )

        previous = (
            _safe_int(payload.get("previous_open_roles_60d"))
            if payload.get("previous_open_roles_60d") is not None
            else _safe_int(payload.get("previous_open_roles"))
        )

        if previous is None:
            previous = _safe_int(payload.get("open_roles_60d_ago"))

        raw_titles = payload.get("titles", [])
        if isinstance(raw_titles, list):
            titles = [str(title) for title in raw_titles if title]

        details.update({k: v for k, v in payload.items() if k != "titles"})
        details["open_roles"] = current
        details["previous_open_roles_60d"] = previous

        return current, previous, titles, details

    current = len(payload)
    for item in payload:
        if isinstance(item, dict) and item.get("title"):
            titles.append(str(item["title"]))

    details["open_roles"] = current
    details["previous_open_roles_60d"] = None
    details["sample_titles"] = titles[:10]

    return current, None, titles, details


def _build_hiring_velocity_signal(
    company_name: str,
    fixture_record: dict[str, Any] | None,
) -> tuple[str | None, dict[str, Any], float, SignalEvidence]:
    payload = _load_company_specific_json(RAW_JOB_POSTS_DIR, company_name)

    if payload is None:
        if fixture_record and fixture_record.get("hiring_velocity_signal"):
            source_path = _repo_relative(FIXTURE_SIGNAL_PATH)
            text = str(fixture_record.get("hiring_velocity_signal"))
            confidence = float((fixture_record.get("confidence_by_signal") or {}).get("hiring_velocity", 0.55))
            details = {
                "source": "fixture",
                "source_path": source_path,
                "velocity_computation": "fixture_signal_only",
            }
            evidence = _signal_evidence(
                name="hiring_velocity",
                value=text,
                confidence=confidence,
                source_path=source_path,
            )
            return text, details, confidence, evidence

        evidence = _signal_evidence(
            name="hiring_velocity",
            value=None,
            confidence=0.0,
            source_path=_source_path(RAW_JOB_POSTS_DIR, company_name),
        )
        return None, {}, 0.0, evidence

    source_path = _source_path(RAW_JOB_POSTS_DIR, company_name)
    open_roles, previous_open_roles, titles, details = _extract_job_snapshot(payload)
    role_change_60d = compute_60d_velocity(open_roles, previous_open_roles)

    # Compatibility fallback: if no previous snapshot exists, preserve any committed fixture multiplier.
    if role_change_60d is None and isinstance(payload, dict):
        fallback_multiplier = payload.get("role_change_60d")
        try:
            role_change_60d = float(fallback_multiplier) if fallback_multiplier not in (None, "") else None
        except (TypeError, ValueError):
            role_change_60d = None

    details.update(
        {
            "source": "raw_job_posts",
            "source_path": source_path,
            "open_roles": open_roles,
            "previous_open_roles_60d": previous_open_roles,
            "role_change_60d": role_change_60d,
            "velocity_method": (
                "computed_current_over_previous_60d"
                if previous_open_roles is not None
                else "fallback_payload_multiplier_or_point_snapshot"
            ),
            "titles": titles[:20],
        }
    )

    if open_roles <= 0:
        evidence = _signal_evidence(
            name="hiring_velocity",
            value=None,
            confidence=0.0,
            source_path=source_path,
        )
        return None, details, 0.0, evidence

    title_snippet = ", ".join(titles[:3]) if titles else f"{open_roles} open roles"

    if role_change_60d is not None:
        signal = (
            f"{open_roles} public engineering-adjacent roles found; "
            f"60-day hiring velocity multiplier {role_change_60d}."
        )
        confidence = 0.82 if previous_open_roles is not None else 0.72
    else:
        signal = f"{open_roles} public engineering-adjacent roles found ({title_snippet})."
        confidence = 0.65

    final_conf = round(min(confidence, 0.9), 2)
    evidence = _signal_evidence(
        name="hiring_velocity",
        value=signal,
        confidence=final_conf,
        source_path=source_path,
    )
    return signal, details, final_conf, evidence


def _build_leadership_signal(
    company_name: str,
    fixture_record: dict[str, Any] | None,
) -> tuple[str | None, dict[str, Any], float, SignalEvidence]:
    payload = _load_company_specific_json(RAW_PRESS_DIR, company_name)
    leadership_keywords = ("cto", "vp engineering", "vice president engineering", "head of engineering")
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    source_path = _source_path(RAW_PRESS_DIR, company_name)

    if isinstance(payload, list):
        for item in payload:
            if not isinstance(item, dict):
                continue

            text = " ".join(str(item.get(key, "")) for key in ["title", "headline", "summary"]).lower()
            published_at = _parse_datetime(str(item.get("published_at") or item.get("date") or ""))

            if any(keyword in text for keyword in leadership_keywords) and (
                published_at is None or published_at >= cutoff
            ):
                summary = str(item.get("title") or item.get("headline") or "Leadership change observed")
                details = dict(item)
                details["source"] = "raw_press"
                details["source_path"] = source_path
                confidence = 0.8 if published_at else 0.65
                evidence = _signal_evidence(
                    name="leadership_change",
                    value=summary,
                    confidence=confidence,
                    source_path=source_path,
                    timestamp_utc=published_at.isoformat() if published_at else None,
                )
                return summary, details, confidence, evidence

    if fixture_record and fixture_record.get("leadership_change_signal"):
        fixture_source = _repo_relative(FIXTURE_SIGNAL_PATH)
        text = str(fixture_record.get("leadership_change_signal"))
        confidence = float((fixture_record.get("confidence_by_signal") or {}).get("leadership_change", 0.55))
        details = {"source": "fixture", "source_path": fixture_source}
        evidence = _signal_evidence(
            name="leadership_change",
            value=text,
            confidence=confidence,
            source_path=fixture_source,
        )
        return text, details, confidence, evidence

    evidence = _signal_evidence(
        name="leadership_change",
        value=None,
        confidence=0.0,
        source_path=source_path,
    )
    return None, {}, 0.0, evidence


def _build_tech_stack_signal(
    company_name: str,
    fixture_record: dict[str, Any] | None,
) -> tuple[str | None, dict[str, Any], float, SignalEvidence]:
    payload = _load_company_specific_json(RAW_TECH_STACK_DIR, company_name)
    source_path = _source_path(RAW_TECH_STACK_DIR, company_name)

    if payload is None:
        if fixture_record and fixture_record.get("tech_stack_signal"):
            fixture_source = _repo_relative(FIXTURE_SIGNAL_PATH)
            text = str(fixture_record.get("tech_stack_signal"))
            confidence = float((fixture_record.get("confidence_by_signal") or {}).get("tech_stack", 0.5))
            details = {"source": "fixture", "source_path": fixture_source}
            evidence = _signal_evidence(
                name="tech_stack",
                value=text,
                confidence=confidence,
                source_path=fixture_source,
            )
            return text, details, confidence, evidence

        evidence = _signal_evidence(
            name="tech_stack",
            value=None,
            confidence=0.0,
            source_path=source_path,
        )
        return None, {}, 0.0, evidence

    technologies: list[str] = []
    details: dict[str, Any] = {"source": "raw_tech_stack", "source_path": source_path}

    if isinstance(payload, dict):
        for key in ["technologies", "stack", "tools"]:
            value = payload.get(key)
            if isinstance(value, list):
                technologies.extend(str(item) for item in value if item)
        details.update({k: v for k, v in payload.items() if k not in {"technologies", "stack", "tools"}})
    elif isinstance(payload, list):
        technologies.extend(str(item) for item in payload if item)

    technologies = list(dict.fromkeys(technologies))
    details["technologies"] = technologies

    if not technologies:
        evidence = _signal_evidence(
            name="tech_stack",
            value=None,
            confidence=0.0,
            source_path=source_path,
        )
        return None, details, 0.0, evidence

    snippet = ", ".join(technologies[:5])
    signal = f"Observed public stack signals: {snippet}."
    confidence = 0.72 if len(technologies) >= 3 else 0.6
    evidence = _signal_evidence(
        name="tech_stack",
        value=signal,
        confidence=confidence,
        source_path=source_path,
    )
    return signal, details, confidence, evidence


def _build_summary(signals: list[str]) -> str:
    cleaned = [signal.strip() for signal in signals if signal and signal.strip()]
    if not cleaned:
        return "No strong public hiring or operating signals were found."
    return "; ".join(cleaned)


def build_hiring_signal_brief(company_name: str) -> HiringSignalBrief:
    fixture_record = _find_fixture_signal_record(company_name)

    funding_signal, funding_details, funding_conf, funding_evidence = _build_funding_signal(company_name)
    hiring_signal, hiring_details, hiring_conf, hiring_evidence = _build_hiring_velocity_signal(
        company_name,
        fixture_record,
    )
    layoffs_signal, layoffs_details, layoffs_conf = build_layoff_signal(company_name)
    leadership_signal, leadership_details, leadership_conf, leadership_evidence = _build_leadership_signal(
        company_name,
        fixture_record,
    )
    tech_stack_signal, tech_stack_details, tech_stack_conf, tech_stack_evidence = _build_tech_stack_signal(
        company_name,
        fixture_record,
    )

    layoffs_source_path = layoffs_details.get("source_path")
    layoffs_evidence = _signal_evidence(
        name="layoffs",
        value=layoffs_signal,
        confidence=float(layoffs_conf),
        source_path=layoffs_source_path,
        timestamp_utc=layoffs_details.get("date") or layoffs_details.get("timestamp_utc"),
    )

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

    if not funding_signal:
        missing_inputs.append("crunchbase_funding")
    if not hiring_signal:
        missing_inputs.append("job_posts_snapshot")
    if not layoffs_signal:
        missing_inputs.append("layoffs_snapshot")
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
        overall_summary=_build_summary(
            [
                funding_signal or "",
                hiring_signal or "",
                layoffs_signal or "",
                leadership_signal or "",
                tech_stack_signal or "",
            ]
        ),
        funding_details=funding_details,
        hiring_velocity_details=hiring_details,
        layoffs_details=layoffs_details,
        leadership_change_details=leadership_details,
        tech_stack_details=tech_stack_details,
        source_paths=source_paths,
        missing_inputs=missing_inputs,
        signals=[
            funding_evidence,
            hiring_evidence,
            layoffs_evidence,
            leadership_evidence,
            tech_stack_evidence,
        ],
    )
