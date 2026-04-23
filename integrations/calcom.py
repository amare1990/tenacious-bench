from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
import httpx


load_dotenv()

STUB_PATH = Path(__file__).resolve().parent.parent / "data" / "calcom_stub.jsonl"


class CalcomClientError(Exception):
    pass


def _get_env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)


def get_mode() -> str:
    return (_get_env("CALCOM_MODE", "stub") or "stub").strip().lower()


def _append_stub(event_type: str, payload: dict[str, Any]) -> None:
    STUB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with STUB_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"event": event_type, "payload": payload}) + "\n")


def propose_time_slots() -> list[str]:
    api_key = _get_env("CALCOM_API_KEY")
    base_url = (_get_env("CALCOM_BASE_URL") or "").rstrip("/")
    event_type_id = _get_env("CALCOM_DEFAULT_EVENT_TYPE_ID")

    if not api_key or not base_url or not event_type_id:
        raise CalcomClientError("Cal.com env vars missing for slot lookup")

    start_date = datetime.now(timezone.utc).date().isoformat()
    end_date = (datetime.now(timezone.utc).date() + timedelta(days=7)).isoformat()

    url = (
        f"{base_url}/slots"
        f"?eventTypeId={int(event_type_id)}"
        f"&start={start_date}"
        f"&end={end_date}"
        f"&timeZone=Africa/Addis_Ababa"
    )

    # headers = {
    #     "Authorization": f"Bearer {api_key}",
    # }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "cal-api-version": "2026-02-25",
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.get(url, headers=headers)

    # If the API reports not found for the eventType or route, return empty slots
    # so callers can fall back instead of crashing the process.
    if response.status_code == 404:
        return []

    if response.status_code >= 400:
        raise CalcomClientError(f"Cal.com slots API error {response.status_code}: {response.text}")

    data = response.json().get("data", {})
    slots: list[str] = []
    for _, day_slots in data.items():
        for slot in day_slots:
            start_value = slot.get("start")
            if start_value:
                slots.append(start_value)

    # Do not raise here; return empty list to let caller decide fallback behavior
    if not slots:
        return []

    return slots[:3]

def create_booking(
    *,
    company_name: str,
    email: str,
    selected_time: str | None = None,
) -> dict[str, Any]:
    mode = get_mode()

    payload = {
        "company_name": company_name,
        "email": email,
        "selected_time": selected_time,
    }

    if mode == "stub":
        _append_stub("create_booking", payload)
        return {
            "status": "stubbed",
            "message": "Booking recorded locally.",
            "payload": payload,
        }

    if mode != "live":
        raise CalcomClientError(f"Unsupported CALCOM_MODE: {mode}")

    return _create_booking_live(payload)


def _create_booking_live(payload: dict[str, Any]) -> dict[str, Any]:
    api_key = _get_env("CALCOM_API_KEY")
    base_url = (_get_env("CALCOM_BASE_URL") or "").rstrip("/")
    event_type_id = _get_env("CALCOM_DEFAULT_EVENT_TYPE_ID")

    if not api_key:
        raise CalcomClientError("CALCOM_API_KEY required for live mode")
    if not base_url:
        raise CalcomClientError("CALCOM_BASE_URL required for live mode")
    if not event_type_id:
        raise CalcomClientError("CALCOM_DEFAULT_EVENT_TYPE_ID required for live mode")
    if not payload.get("selected_time"):
        raise CalcomClientError("selected_time is required for live booking")

    url = f"{base_url}/bookings"

    # headers = {
    #     "Authorization": f"Bearer {api_key}",
    #     "Content-Type": "application/json",
    # }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "cal-api-version": "2026-02-25",
    }

    request_body = {
        "start": payload["selected_time"],
        "attendee": {
            "name": payload["company_name"],
            "timeZone": "Africa/Addis_Ababa",
            "language": "en",
            "email": payload["email"],
        },
        "eventTypeId": int(event_type_id),
        "metadata": {
            "company_name": payload["company_name"],
            "source": "conversion-engine",
        },
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, headers=headers, json=request_body)

    if response.status_code >= 400:
        raise CalcomClientError(
            f"Cal.com API error {response.status_code}: {response.text}"
        )

    data = response.json()

    return {
        "status": "sent",
        "selected_time": payload["selected_time"],
        "booking_id": data.get("data", {}).get("id") or data.get("id"),
        "booking_url": data.get("data", {}).get("bookingUrl") or data.get("bookingUrl"),
        "response": data,
    }
