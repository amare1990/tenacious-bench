"""
Inbound email webhook handler.

Purpose:
- Accept Resend/MailerSend-style inbound reply events.
- Normalize the payload into the agent's reply-processing shape.
- Route the reply into the central orchestrator.
- Preserve email-first architecture: email is the primary channel; SMS remains gated
  behind prior email engagement.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from agent.orchestrator import process_reply

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/email", tags=["email-webhooks"])


class NormalizedEmailReply(BaseModel):
    channel: str = "email"
    provider: str
    provider_event_id: str | None = None
    from_email: str
    to_email: str | None = None
    subject: str | None = None
    text: str
    html: str | None = None
    thread_id: str | None = None
    prospect_id: str | None = None
    received_at_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    raw_event: dict[str, Any]


def _first_string(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, list) and value:
        first = value[0]
        if isinstance(first, str):
            return first.strip()
        if isinstance(first, dict):
            return (
                first.get("email")
                or first.get("address")
                or first.get("from_email")
                or first.get("to_email")
            )
    if isinstance(value, dict):
        return value.get("email") or value.get("address")
    return None


def _normalize_resend(payload: dict[str, Any]) -> NormalizedEmailReply:
    data = payload.get("data", payload)

    from_email = (
        _first_string(data.get("from"))
        or _first_string(data.get("from_email"))
        or _first_string(data.get("sender"))
    )
    to_email = (
        _first_string(data.get("to"))
        or _first_string(data.get("to_email"))
        or _first_string(data.get("recipient"))
    )

    text = (
        data.get("text")
        or data.get("text_body")
        or data.get("plain")
        or data.get("body")
        or ""
    )

    if not from_email:
        raise ValueError("Missing sender email in Resend inbound payload.")
    if not str(text).strip():
        raise ValueError("Missing reply text in Resend inbound payload.")

    return NormalizedEmailReply(
        provider="resend",
        provider_event_id=str(
            payload.get("id")
            or data.get("id")
            or data.get("email_id")
            or data.get("message_id")
            or ""
        )
        or None,
        from_email=from_email,
        to_email=to_email,
        subject=data.get("subject"),
        text=str(text).strip(),
        html=data.get("html") or data.get("html_body"),
        thread_id=(
            data.get("thread_id")
            or data.get("headers", {}).get("References")
            or data.get("headers", {}).get("In-Reply-To")
        ),
        prospect_id=(
            data.get("metadata", {}).get("prospect_id")
            if isinstance(data.get("metadata"), dict)
            else None
        ),
        raw_event=payload,
    )


def _normalize_mailersend(payload: dict[str, Any]) -> NormalizedEmailReply:
    data = payload.get("data", payload)

    from_email = (
        _first_string(data.get("from"))
        or _first_string(data.get("sender"))
        or _first_string(data.get("from_email"))
    )
    to_email = (
        _first_string(data.get("to"))
        or _first_string(data.get("recipient"))
        or _first_string(data.get("to_email"))
    )

    text = (
        data.get("text")
        or data.get("text_body")
        or data.get("body")
        or data.get("message", {}).get("text")
        if isinstance(data.get("message"), dict)
        else None
    ) or ""

    if not from_email:
        raise ValueError("Missing sender email in MailerSend inbound payload.")
    if not str(text).strip():
        raise ValueError("Missing reply text in MailerSend inbound payload.")

    return NormalizedEmailReply(
        provider="mailersend",
        provider_event_id=str(payload.get("id") or data.get("id") or "") or None,
        from_email=from_email,
        to_email=to_email,
        subject=data.get("subject") or data.get("message", {}).get("subject"),
        text=str(text).strip(),
        html=data.get("html") or data.get("html_body"),
        thread_id=data.get("thread_id") or data.get("message_id"),
        prospect_id=(
            data.get("metadata", {}).get("prospect_id")
            if isinstance(data.get("metadata"), dict)
            else None
        ),
        raw_event=payload,
    )

def _extract_company_name(reply: NormalizedEmailReply) -> str | None:
    raw = reply.raw_event or {}

    data = raw.get("data", raw)
    metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}

    for key in ("company_name", "company", "account_name"):
        value = metadata.get(key) or data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    if reply.from_email and "@" in reply.from_email:
        domain = reply.from_email.split("@", 1)[1].split(".", 1)[0]
        return domain.replace("-", " ").title()

    return None

def normalize_email_webhook(payload: dict[str, Any]) -> NormalizedEmailReply:
    provider_hint = str(
        payload.get("provider")
        or payload.get("source")
        or payload.get("type")
        or ""
    ).lower()

    if "mailersend" in provider_hint:
        return _normalize_mailersend(payload)

    return _normalize_resend(payload)


@router.post("/inbound")
async def inbound_email_reply(request: Request) -> dict[str, Any]:
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload.") from exc

    try:
        reply = normalize_email_webhook(payload)
    except ValueError as exc:
        logger.warning("Rejected inbound email webhook: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    company_name = (
        reply.prospect_id
        or _extract_company_name(reply)
        or reply.from_email
    )

    try:
        result = process_reply(
            company_name=company_name,
            reply_text=reply.text,
            recipient=reply.from_email,
            book=False,
        )
    except Exception as exc:
        logger.exception("Email reply processing failed.")
        raise HTTPException(status_code=500, detail="Email reply processing failed.") from exc

    return {
        "ok": True,
        "channel": "email",
        "provider": reply.provider,
        "from_email": reply.from_email,
        "company_name": company_name,
        "thread_id": reply.thread_id,
        "result": result,
    }
