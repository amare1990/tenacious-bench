from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import httpx


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
    """
    Return 3 future ISO timestamps as candidate slots.
    """
    now = datetime.utcnow()

    return [
        (now + timedelta(days=1, hours=2)).isoformat(),
        (now + timedelta(days=2, hours=3)).isoformat(),
        (now + timedelta(days=3, hours=1)).isoformat(),
    ]


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

    if not api_key:
        raise CalcomClientError("CALCOM_API_KEY required for live mode")

    url = f"{base_url}/bookings"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    request_body = {
        "responses": {
            "name": payload["company_name"],
            "email": payload["email"],
        },
        "start": payload["selected_time"],
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, headers=headers, json=request_body)

    if response.status_code >= 400:
        raise CalcomClientError(
            f"Cal.com API error {response.status_code}: {response.text}"
        )

    return {
        "status": "sent",
        "message": "Booking created in Cal.com",
        "response": response.json(),
    }
