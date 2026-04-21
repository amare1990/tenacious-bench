from __future__ import annotations

import os
import json
from typing import Any

import httpx


class EmailClientError(Exception):
    pass


def _get_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    return value


def get_email_mode() -> str:
    return (_get_env("EMAIL_MODE", "draft") or "draft").strip().lower()


def get_email_provider() -> str:
    return (_get_env("EMAIL_PROVIDER", "console") or "console").strip().lower()


def send_email(
    *,
    to_email: str,
    subject: str,
    body: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Send or stage an email depending on EMAIL_MODE.

    Supported modes:
    - draft: return a structured draft, do not send
    - live: send using configured provider
    """

    email_mode = get_email_mode()
    email_provider = get_email_provider()

    sender_name = _get_env("OUTBOUND_SENDER_NAME", "Tenacious") or "Tenacious"
    sender_email = _get_env("OUTBOUND_SENDER_EMAIL", "noreply@example.com") or "noreply@example.com"

    payload = {
        "from_name": sender_name,
        "from_email": sender_email,
        "to_email": to_email,
        "subject": subject,
        "body": body,
        "metadata": metadata or {},
        "mode": email_mode,
        "provider": email_provider,
    }

    if email_mode == "draft":
        return {
            "status": "draft",
            "provider": email_provider,
            "message": "Email generated in draft mode; not sent.",
            "payload": payload,
        }

    if email_mode != "live":
        raise EmailClientError(f"Unsupported EMAIL_MODE: {email_mode}")

    if email_provider == "console":
        print("\n=== LIVE SEND (console provider) ===")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return {
            "status": "sent",
            "provider": "console",
            "message": "Email simulated via console provider.",
            "payload": payload,
        }

    if email_provider == "resend":
        return _send_via_resend(payload)

    raise EmailClientError(f"Unsupported EMAIL_PROVIDER: {email_provider}")


def _send_via_resend(payload: dict[str, Any]) -> dict[str, Any]:
    api_key = _get_env("RESEND_API_KEY")
    if not api_key:
        raise EmailClientError("RESEND_API_KEY is required for EMAIL_PROVIDER=resend")

    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    request_body = {
        "from": f"{payload['from_name']} <{payload['from_email']}>",
        "to": [payload["to_email"]],
        "subject": payload["subject"],
        "text": payload["body"],
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, headers=headers, json=request_body)

    if response.status_code >= 400:
        raise EmailClientError(
            f"Resend API error {response.status_code}: {response.text}"
        )

    return {
        "status": "sent",
        "provider": "resend",
        "message": "Email sent successfully via Resend.",
        "payload": payload,
        "response": response.json(),
    }
