from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

STUB_PATH = Path(__file__).resolve().parent.parent / 'data' / 'sms_stub.jsonl'


class SMSClientError(Exception):
    pass


def _get_env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)


def get_sms_mode() -> str:
    return (_get_env('SMS_MODE', 'stub') or 'stub').strip().lower()


def send_sms(*, to_phone: str, body: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {
        'to_phone': to_phone,
        'body': body,
        'metadata': metadata or {},
        'mode': get_sms_mode(),
    }
    STUB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with STUB_PATH.open('a', encoding='utf-8') as f:
        f.write(json.dumps(payload, ensure_ascii=False) + '\n')
    return {'status': 'stubbed', 'payload': payload, 'message': 'SMS recorded locally.'}
