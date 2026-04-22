from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import uuid


TRACE_PATH = Path(__file__).resolve().parent.parent / "data" / "trace_log.jsonl"


def _make_json_safe(value: Any) -> Any:
    """Recursively convert values into JSON-serializable structures."""
    if hasattr(value, "model_dump"):
        return _make_json_safe(value.model_dump())

    if isinstance(value, dict):
        return {str(k): _make_json_safe(v) for k, v in value.items()}

    if isinstance(value, list):
        return [_make_json_safe(v) for v in value]

    if isinstance(value, tuple):
        return [_make_json_safe(v) for v in value]

    return value


def append_trace(record: dict[str, Any]) -> str:
    """Append one structured trace record to the JSONL trace log."""
    TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)

    record = _make_json_safe(dict(record))
    record.setdefault("trace_id", str(uuid.uuid4()))
    record.setdefault("timestamp_utc", datetime.now(timezone.utc).isoformat())

    with TRACE_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

    return str(record["trace_id"])


def log_trace(event_type: str, payload: dict[str, Any]) -> str:
    """Convenience wrapper for appending an event-style trace."""
    return append_trace(
        {
            "event_type": event_type,
            "payload": payload,
        }
    )
