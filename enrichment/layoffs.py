from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from enrichment.source_inventory import RAW_DIR


LAYOFFS_PATH = RAW_DIR / "layoffs" / "layoffs.csv"


def _normalize_name(name: str) -> str:
    return " ".join(name.strip().lower().split())


def _load_layoff_rows() -> list[dict[str, Any]]:
    if not LAYOFFS_PATH.exists() or LAYOFFS_PATH.stat().st_size == 0:
        return []

    with LAYOFFS_PATH.open("r", encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f, delimiter=";", quotechar='"')
        rows = []
        for row in reader:
            cleaned = {str(k).strip().strip('"'): (str(v).strip().strip('"') if v is not None else None) for k, v in row.items()}
            rows.append(cleaned)
        return rows


def find_recent_layoff(company_name: str, lookback_days: int = 120) -> dict[str, Any] | None:
    normalized_query = _normalize_name(company_name)
    rows = _load_layoff_rows()
    if not rows:
        return None

    cutoff = datetime.now(timezone.utc).date() - timedelta(days=lookback_days)
    matches: list[dict[str, Any]] = []

    for row in rows:
        company = row.get("company") or ""
        normalized_company = _normalize_name(company)
        if normalized_company != normalized_query:
            continue

        layoff_date_raw = row.get("layoff_date")
        if not layoff_date_raw:
            continue

        try:
            layoff_date = datetime.strptime(layoff_date_raw, "%Y-%m-%d").date()
        except ValueError:
            continue

        if layoff_date < cutoff:
            continue

        row = dict(row)
        row["layoff_date"] = layoff_date.isoformat()
        matches.append(row)

    if not matches:
        return None

    matches.sort(key=lambda item: item.get("layoff_date", ""), reverse=True)
    return matches[0]


def build_layoff_signal(company_name: str, lookback_days: int = 120) -> tuple[str | None, dict[str, Any], float]:
    match = find_recent_layoff(company_name, lookback_days=lookback_days)
    if match is None:
        return None, {}, 0.0

    total_laid_off = match.get("total_laid_off") or "unknown"
    percentage_laid_off = match.get("percentage_laid_off") or "unknown"
    stage = match.get("stage") or "unknown stage"
    layoff_date = match.get("layoff_date")

    signal = (
        f"Layoff signal found on {layoff_date}: {total_laid_off} employees affected "
        f"({percentage_laid_off}% disclosed), stage {stage}."
    )

    confidence = 0.85
    if percentage_laid_off not in {None, "", "0", "0.0", 0}:
        confidence += 0.05

    details = {
        "company": match.get("company"),
        "location": match.get("location"),
        "industry": match.get("industry"),
        "total_laid_off": total_laid_off,
        "percentage_laid_off": percentage_laid_off,
        "layoff_date": layoff_date,
        "stage": stage,
        "country": match.get("country"),
        "funds_raised_millions": match.get("funds_raised_millions"),
        "source_path": str(LAYOFFS_PATH.relative_to(Path(__file__).resolve().parent.parent)),
    }

    return signal, details, min(round(confidence, 2), 0.95)
