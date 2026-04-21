from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from briefs.models import ConversationState


STATE_PATH = Path(__file__).resolve().parent.parent / "data" / "conversations.jsonl"


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


def save_conversation_state(
    *,
    company_name: str,
    recipient: str | None,
    state: ConversationState,
    metadata: dict[str, Any] | None = None,
) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "company_name": company_name,
        "recipient": recipient,
        "state": _json_safe(state),
        "metadata": _json_safe(metadata or {}),
    }

    with STATE_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_latest_conversation_state(
    *,
    company_name: str,
    recipient: str | None = None,
) -> ConversationState | None:
    if not STATE_PATH.exists():
        return None

    latest_match: dict[str, Any] | None = None

    with STATE_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            if record.get("company_name") != company_name:
                continue

            if recipient is not None and record.get("recipient") != recipient:
                continue

            latest_match = record

    if latest_match is None:
        return None

    state_data = latest_match.get("state")
    if not isinstance(state_data, dict):
        return None

    return ConversationState(**state_data)
