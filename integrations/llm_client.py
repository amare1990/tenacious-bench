from __future__ import annotations

import json
import os
from typing import Any

import httpx


class LLMClientError(Exception):
    pass


def _get_env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)


def is_llm_reply_analysis_enabled() -> bool:
    value = (_get_env("ENABLE_LLM_REPLY_ANALYSIS", "false") or "false").strip().lower()
    return value in {"1", "true", "yes", "on"}


def call_openrouter_json(
    *,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.1,
) -> dict[str, Any]:
    api_key = _get_env("OPENROUTER_API_KEY")
    base_url = (_get_env("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1") or "https://openrouter.ai/api/v1").rstrip("/")
    model = _get_env("OPENROUTER_MODEL", "openrouter/openai/gpt-4o-mini") or "openrouter/openai/gpt-4o-mini"
    timeout_seconds = float(_get_env("LLM_TIMEOUT_SECONDS", "30") or "30")

    if not api_key:
        raise LLMClientError("OPENROUTER_API_KEY is not set")

    url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    request_body = {
        "model": model,
        "temperature": temperature,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    with httpx.Client(timeout=timeout_seconds) as client:
        response = client.post(url, headers=headers, json=request_body)

    if response.status_code >= 400:
        raise LLMClientError(
            f"OpenRouter API error {response.status_code}: {response.text}"
        )

    data = response.json()

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMClientError("Malformed OpenRouter response structure") from exc

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise LLMClientError(f"Model did not return valid JSON: {content}") from exc

    if not isinstance(parsed, dict):
        raise LLMClientError("Model returned JSON that is not an object")

    return parsed
