from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from datetime import datetime, timezone

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
    contact_email: str | None = None,
    contact_first_name: str | None = None,
    contact_last_name: str | None = None,
) -> dict[str, Any]:
    return {
        "company_name": company.company_name,
        "industry": company.industry,
        "employee_count": company.employee_count,
        "location": company.location,
        "funding_stage": company.funding_stage,
        "last_funding_date": company.last_funding_date,
        "contact_email": contact_email,
        "contact_first_name": contact_first_name,
        "contact_last_name": contact_last_name,
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
        "enrichment_timestamp_utc": datetime.now(timezone.utc).isoformat(),
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


def log_engagement_note(
    company_name: str,
    note: str,
    metadata: dict[str, Any] | None = None,
    *,
    contact_id: str | None = None,
    company_id: str | None = None,
) -> dict[str, Any]:
    mode = get_hubspot_mode()
    payload = {
        "company_name": company_name,
        "note": note,
        "metadata": _json_safe(metadata or {}),
        "contact_id": contact_id,
        "company_id": company_id,
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


def _headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }


def _search_contact_by_email(
    client: httpx.Client,
    *,
    base_url: str,
    headers: dict[str, str],
    email: str,
) -> dict[str, Any] | None:
    url = f"{base_url}/crm/v3/objects/contacts/search"
    body = {
        "filterGroups": [
            {
                "filters": [
                    {
                        "propertyName": "email",
                        "operator": "EQ",
                        "value": email,
                    }
                ]
            }
        ],
        "properties": ["email", "firstname", "lastname"],
        "limit": 1,
    }
    response = client.post(url, headers=headers, json=body)
    if response.status_code >= 400:
        raise HubSpotClientError(f"HubSpot contact search error {response.status_code}: {response.text}")
    data = response.json()
    results = data.get("results", [])
    return results[0] if results else None


def _create_contact(
    client: httpx.Client,
    *,
    base_url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    email = payload.get("contact_email")
    if not email:
        return None

    existing = _search_contact_by_email(client, base_url=base_url, headers=headers, email=email)
    if existing:
        return existing

    url = f"{base_url}/crm/v3/objects/contacts"
    body = {
        "properties": {
            "email": email,
            "firstname": payload.get("contact_first_name") or "Synthetic",
            "lastname": payload.get("contact_last_name") or (payload.get("company_name") or "Lead"),
            "lifecyclestage": "lead",
        }
    }
    response = client.post(url, headers=headers, json=body)
    if response.status_code >= 400:
        raise HubSpotClientError(f"HubSpot contact create error {response.status_code}: {response.text}")
    return response.json()


def _search_company_by_name(
    client: httpx.Client,
    *,
    base_url: str,
    headers: dict[str, str],
    company_name: str,
) -> dict[str, Any] | None:
    url = f"{base_url}/crm/v3/objects/companies/search"
    body = {
        "filterGroups": [
            {
                "filters": [
                    {
                        "propertyName": "name",
                        "operator": "EQ",
                        "value": company_name,
                    }
                ]
            }
        ],
        "properties": ["name", "industry", "city"],
        "limit": 1,
    }
    response = client.post(url, headers=headers, json=body)
    if response.status_code >= 400:
        raise HubSpotClientError(f"HubSpot company search error {response.status_code}: {response.text}")
    data = response.json()
    results = data.get("results", [])
    return results[0] if results else None


def _map_hubspot_industry(value: str | None) -> str | None:
    if not value:
        return None

    normalized = value.strip().lower()

    mapping = {
        "fintech": "FINANCIAL_SERVICES",
        "financial technology": "FINANCIAL_SERVICES",
        "developer tools": "COMPUTER_SOFTWARE",
        "sales technology": "COMPUTER_SOFTWARE",
        "saas": "COMPUTER_SOFTWARE",
    }

    return mapping.get(normalized)

def _create_company(
    client: httpx.Client,
    *,
    base_url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
) -> dict[str, Any]:
    company_name = payload.get("company_name")
    if not company_name:
        raise HubSpotClientError("company_name is required to create HubSpot company")

    existing = _search_company_by_name(client, base_url=base_url, headers=headers, company_name=company_name)
    if existing:
        return existing

    url = f"{base_url}/crm/v3/objects/companies"
    body = {
        "properties": {
            "name": company_name,
            "description": payload.get("competitor_gap_summary"),
            "industry": _map_hubspot_industry(payload.get("industry")),
            "city": payload.get("location"),
        }
    }
    response = client.post(url, headers=headers, json=body)
    if response.status_code >= 400:
        raise HubSpotClientError(f"HubSpot company create error {response.status_code}: {response.text}")
    return response.json()


def _associate_contact_to_company(
    client: httpx.Client,
    *,
    base_url: str,
    headers: dict[str, str],
    contact_id: str,
    company_id: str,
) -> dict[str, Any]:
    url = f"{base_url}/crm/v3/objects/contacts/{contact_id}/associations/companies/{company_id}/contact_to_company"
    response = client.put(url, headers=headers)
    if response.status_code >= 400:
        raise HubSpotClientError(f"HubSpot association error {response.status_code}: {response.text}")
    return {
        "status_code": response.status_code,
        "text": response.text,
    }


def _upsert_lead_record_live(payload: dict[str, Any]) -> dict[str, Any]:
    access_token = _get_env("HUBSPOT_ACCESS_TOKEN")
    base_url = (_get_env("HUBSPOT_BASE_URL", "https://api.hubapi.com") or "https://api.hubapi.com").rstrip("/")

    if not access_token:
        raise HubSpotClientError("HUBSPOT_ACCESS_TOKEN is required for HUBSPOT_MODE=live")

    headers = _headers(access_token)

    with httpx.Client(timeout=30.0) as client:
        contact = _create_contact(client, base_url=base_url, headers=headers, payload=payload)
        company = _create_company(client, base_url=base_url, headers=headers, payload=payload)

        association_result = None
        if contact and company:
            association_result = _associate_contact_to_company(
                client,
                base_url=base_url,
                headers=headers,
                contact_id=str(contact["id"]),
                company_id=str(company["id"]),
            )

    return {
        "status": "sent",
        "mode": "live",
        "message": "Lead record sent to HubSpot.",
        "payload": payload,
        "contact_response": contact,
        "company_response": company,
        "association_response": association_result,
        "contact_id": None if not contact else str(contact["id"]),
        "company_id": str(company["id"]),
    }


def _associate_note(
    client: httpx.Client,
    *,
    base_url: str,
    headers: dict[str, str],
    note_id: str,
    object_type: str,
    object_id: str,
) -> dict[str, Any]:
    url = f"{base_url}/crm/v3/objects/notes/{note_id}/associations/{object_type}/{object_id}/note_to_{object_type}"
    response = client.put(url, headers=headers)
    if response.status_code >= 400:
        raise HubSpotClientError(f"HubSpot note association error {response.status_code}: {response.text}")
    return {
        "status_code": response.status_code,
        "text": response.text,
    }


def _log_engagement_note_live(payload: dict[str, Any]) -> dict[str, Any]:
    access_token = _get_env("HUBSPOT_ACCESS_TOKEN")
    base_url = (_get_env("HUBSPOT_BASE_URL", "https://api.hubapi.com") or "https://api.hubapi.com").rstrip("/")

    if not access_token:
        raise HubSpotClientError("HUBSPOT_ACCESS_TOKEN is required for HUBSPOT_MODE=live")

    url = f"{base_url}/crm/v3/objects/notes"
    headers = _headers(access_token)

    request_body = {
        "properties": {
            "hs_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "hs_note_body": payload["note"],
        }
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, headers=headers, json=request_body)

        if response.status_code >= 400:
            raise HubSpotClientError(f"HubSpot API error {response.status_code}: {response.text}")

        note_response = response.json()
        note_id = str(note_response["id"])

        # associations: dict[str, Any] = {}
        associations = {}
        # if payload.get("contact_id"):
        #     associations["contact"] = _associate_note(
        #         client,
        #         base_url=base_url,
        #         headers=headers,
        #         note_id=note_id,
        #         object_type="contacts",
        #         object_id=str(payload["contact_id"]),
        #     )
        # if payload.get("company_id"):
        #     associations["company"] = _associate_note(
        #         client,
        #         base_url=base_url,
        #         headers=headers,
        #         note_id=note_id,
        #         object_type="companies",
        #         object_id=str(payload["company_id"]),
        #     )

    # url = f"{base_url}/crm/v3/objects/notes/{note_id}/associations/{object_type}/{object_id}/note_to_{object_type}"
    return {
        "status": "sent",
        "mode": "live",
        "message": "Engagement note sent to HubSpot.",
        "payload": payload,
        "response": note_response,
        "note_id": note_id,
        "associations": associations,
    }

def log_booking_update(
    *,
    company_name: str,
    contact_id: str | None,
    company_id: str | None,
    booking_payload: dict[str, Any],
) -> dict[str, Any]:
    note_lines = [
        f"Booking completed for {company_name}.",
        f"Selected time: {booking_payload.get('selected_time')}",
    ]

    if booking_payload.get("booking_url"):
        note_lines.append(f"Booking URL: {booking_payload['booking_url']}")

    if booking_payload.get("booking_id"):
        note_lines.append(f"Booking ID: {booking_payload['booking_id']}")

    return log_engagement_note(
        company_name=company_name,
        note="\n".join(note_lines),
        metadata={
            "booking_completed": True,
            "selected_time": booking_payload.get("selected_time"),
            "booking_id": booking_payload.get("booking_id"),
            "booking_url": booking_payload.get("booking_url"),
        },
        contact_id=contact_id,
        company_id=company_id,
    )
