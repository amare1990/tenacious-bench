from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx


STUB_LOG_PATH = Path(__file__).resolve().parent.parent / "data" / "hubspot_stub.jsonl"


class HubSpotClientError(Exception):
    pass


def _get_env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)


def get_hubspot_mode() -> str:
    return (_get_env("HUBSPOT_MODE", "stub") or "stub").strip().lower()


def _append_stub_record(event_type: str, payload: dict[str, Any]) -> None:
    STUB_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "event_type": event_type,
        "payload": payload,
    }
    with STUB_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _json_safe(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return _json_safe(value.model_dump())
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [_json_safe(v) for v in value]
    return value


def build_lead_payload(
    *,
    company,
    signals,
    ai_profile,
    gap_brief,
    bench_summary,
    segment_result: dict[str, Any],
    policy_result: dict[str, Any],
    conversation_state,
) -> dict[str, Any]:
    return {
        "company_name": company.company_name,
        "industry": company.industry,
        "employee_count": company.employee_count,
        "location": company.location,
        "funding_stage": company.funding_stage,
        "last_funding_date": company.last_funding_date,
        "segment": segment_result.get("segment"),
        "segment_confidence": segment_result.get("confidence"),
        "segment_rationale": segment_result.get("rationale"),
        "policy_should_contact": policy_result.get("should_contact"),
        "policy_tone_mode": policy_result.get("tone_mode"),
        "policy_claim_strength": policy_result.get("claim_strength"),
        "policy_require_handoff": policy_result.get("require_handoff"),
        "policy_allow_capacity_language": policy_result.get("allow_capacity_language"),
        "ai_maturity_score": ai_profile.score,
        "ai_maturity_confidence": ai_profile.confidence,
        "ai_maturity_rationale": ai_profile.rationale,
        "hiring_signal_summary": signals.summary,
        "competitor_gap_summary": gap_brief.summary,
        "bench_fit": bench_summary.fit,
        "bench_confidence": bench_summary.confidence,
        "bench_notes": bench_summary.notes,
        "conversation_stage": conversation_state.stage,
        "conversation_next_action": conversation_state.next_action,
        "conversation_is_handoff_required": conversation_state.is_handoff_required,
        "conversation_is_qualified": conversation_state.is_qualified,
        "conversation_is_booked": conversation_state.is_booked,
    }


def upsert_lead_record(payload: dict[str, Any]) -> dict[str, Any]:
    mode = get_hubspot_mode()
    safe_payload = _json_safe(payload)

    if mode == "stub":
        _append_stub_record("upsert_lead_record", safe_payload)
        return {
            "status": "stubbed",
            "mode": "stub",
            "message": "Lead record written to local HubSpot stub log.",
            "payload": safe_payload,
        }

    if mode != "live":
        raise HubSpotClientError(f"Unsupported HUBSPOT_MODE: {mode}")

    return _upsert_lead_record_live(safe_payload)


def log_engagement_note(company_name: str, note: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    mode = get_hubspot_mode()
    payload = {
        "company_name": company_name,
        "note": note,
        "metadata": _json_safe(metadata or {}),
    }

    if mode == "stub":
        _append_stub_record("log_engagement_note", payload)
        return {
            "status": "stubbed",
            "mode": "stub",
            "message": "Engagement note written to local HubSpot stub log.",
            "payload": payload,
        }

    if mode != "live":
        raise HubSpotClientError(f"Unsupported HUBSPOT_MODE: {mode}")

    return _log_engagement_note_live(payload)


def _upsert_lead_record_live(payload: dict[str, Any]) -> dict[str, Any]:
    access_token = _get_env("HUBSPOT_ACCESS_TOKEN")
    base_url = (_get_env("HUBSPOT_BASE_URL", "https://api.hubapi.com") or "https://api.hubapi.com").rstrip("/")

    if not access_token:
        raise HubSpotClientError("HUBSPOT_ACCESS_TOKEN is required for HUBSPOT_MODE=live")

    url = f"{base_url}/crm/v3/objects/companies"

    properties = {
        "name": payload.get("company_name"),
        "description": payload.get("competitor_gap_summary"),
        "industry": payload.get("industry"),
        "city": payload.get("location"),
    }

    request_body = {
        "properties": {k: v for k, v in properties.items() if v is not None}
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, headers=headers, json=request_body)

    if response.status_code >= 400:
        raise HubSpotClientError(
            f"HubSpot API error {response.status_code}: {response.text}"
        )

    return {
        "status": "sent",
        "mode": "live",
        "message": "Lead record sent to HubSpot.",
        "payload": payload,
        "response": response.json(),
    }


def _log_engagement_note_live(payload: dict[str, Any]) -> dict[str, Any]:
    access_token = _get_env("HUBSPOT_ACCESS_TOKEN")
    base_url = (_get_env("HUBSPOT_BASE_URL", "https://api.hubapi.com") or "https://api.hubapi.com").rstrip("/")

    if not access_token:
        raise HubSpotClientError("HUBSPOT_ACCESS_TOKEN is required for HUBSPOT_MODE=live")

    url = f"{base_url}/crm/v3/objects/notes"

    request_body = {
        "properties": {
            "hs_note_body": payload["note"],
        }
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, headers=headers, json=request_body)

    if response.status_code >= 400:
        raise HubSpotClientError(
            f"HubSpot API error {response.status_code}: {response.text}"
        )

    return {
        "status": "sent",
        "mode": "live",
        "message": "Engagement note sent to HubSpot.",
        "payload": payload,
        "response": response.json(),
    }
