from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx


STUB_PATH = Path(__file__).resolve().parent.parent / "data" / "sms_stub.jsonl"


class SMSClientError(Exception):
    pass


def _get_env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)


def get_sms_mode() -> str:
    return (_get_env("SMS_MODE", "stub") or "stub").strip().lower()


def get_sms_provider() -> str:
    return (_get_env("SMS_PROVIDER", "stub") or "stub").strip().lower()


def _append_stub(payload: dict[str, Any]) -> None:
    STUB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with STUB_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def send_sms(
    *,
    to_phone: str,
    body: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    mode = get_sms_mode()
    provider = get_sms_provider()

    payload = {
        "to_phone": to_phone,
        "body": body,
        "metadata": metadata or {},
        "mode": mode,
        "provider": provider,
    }

    if mode == "stub":
        _append_stub(payload)
        return {
            "status": "stubbed",
            "provider": provider,
            "payload": payload,
            "message": "SMS recorded locally.",
        }

    if mode != "live":
        raise SMSClientError(f"Unsupported SMS_MODE: {mode}")

    if provider == "africastalking":
        response = _send_via_africastalking(to_phone=to_phone, body=body)
        return {
            "status": "sent",
            "provider": "africastalking",
            "payload": payload,
            "response": response,
            "message": "SMS sent via Africa's Talking.",
        }

    raise SMSClientError(f"Unsupported SMS_PROVIDER: {provider}")


def _send_via_africastalking(*, to_phone: str, body: str) -> dict[str, Any]:
    username = _get_env("AFRICASTALKING_USERNAME")
    api_key = _get_env("AFRICASTALKING_API_KEY")
    url = _get_env(
        "AFRICASTALKING_SMS_URL",
        "https://api.sandbox.africastalking.com/version1/messaging",
    )

    if not username:
        raise SMSClientError("AFRICASTALKING_USERNAME is required for live SMS sending.")
    if not api_key:
        raise SMSClientError("AFRICASTALKING_API_KEY is required for live SMS sending.")
    if not url:
        raise SMSClientError("AFRICASTALKING_SMS_URL is required for live SMS sending.")

    headers = {
        "apiKey": api_key,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }

    data = {
        "username": username,
        "to": to_phone,
        "message": body,
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, headers=headers, data=data)

    if response.status_code >= 400:
        raise SMSClientError(
            f"Africa's Talking SMS error {response.status_code}: {response.text}"
        )

    try:
        return response.json()
    except Exception as exc:
        raise SMSClientError(f"Invalid JSON response from Africa's Talking: {response.text}") from exc
