from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from briefs.models import BenchMatchSummary, HiringSignalBrief, AIMaturityProfile


DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "bench_summary.json"


def _load_bench_data() -> dict[str, Any]:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Bench summary file not found at {DATA_PATH}. "
            "Create data/bench_summary.json first."
        )

    with DATA_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("bench_summary.json must contain a JSON object.")

    return data


def _infer_requested_capabilities(
    signals: HiringSignalBrief,
    ai_profile: AIMaturityProfile,
) -> list[str]:
    requested: list[str] = []

    combined_text = " ".join(
        [
            signals.tech_stack_signal or "",
            signals.hiring_velocity_signal or "",
            signals.summary or "",
            ai_profile.rationale or "",
            " ".join(ai_profile.evidence or []),
        ]
    ).lower()

    keyword_map = {
        "python": "Python",
        "data": "Data Engineering",
        "machine learning": "Machine Learning",
        "ml": "Machine Learning",
        "ai": "Machine Learning",
        "mlops": "MLOps",
        "aws": "AWS",
        "infra": "Infrastructure",
        "infrastructure": "Infrastructure",
        "backend": "Backend Engineering",
    }

    for keyword, capability in keyword_map.items():
        if keyword in combined_text and capability not in requested:
            requested.append(capability)

    if not requested:
        requested.append("Backend Engineering")

    return requested


def build_bench_match_summary(
    signals: HiringSignalBrief,
    ai_profile: AIMaturityProfile,
) -> BenchMatchSummary:
    data = _load_bench_data()

    available_capabilities = data.get("available_capabilities", [])
    bench_notes = data.get("bench_notes", "")

    if not isinstance(available_capabilities, list):
        raise ValueError("available_capabilities must be a list in bench_summary.json")

    requested_capabilities = _infer_requested_capabilities(signals, ai_profile)

    available_set = {cap.strip().lower() for cap in available_capabilities}
    matched = [
        cap for cap in requested_capabilities
        if cap.strip().lower() in available_set
    ]

    match_ratio = len(matched) / max(len(requested_capabilities), 1)
    fit = match_ratio >= 0.6

    confidence = round(min(0.45 + match_ratio * 0.45, 0.95), 2)

    notes = (
        f"Requested capabilities inferred: {', '.join(requested_capabilities)}. "
        f"Matched capabilities: {', '.join(matched) if matched else 'none'}. "
        f"{bench_notes}"
    )

    return BenchMatchSummary(
        requested_capabilities=requested_capabilities,
        available_capabilities=available_capabilities,
        fit=fit,
        confidence=confidence,
        notes=notes,
    )
