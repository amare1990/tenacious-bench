from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from enrichment.source_inventory import slugify_company_name


RAW_JOB_POSTS_DIR = Path("data/raw/job_posts")

COMPANY_CAREERS_URLS = {
    "Ramp": [
        "https://ramp.com/careers",
        "https://ramp.com/careers/jobs",
    ],
    "Clay": [
        "https://www.clay.com/careers",
    ],
    "Retool": [
        "https://retool.com/careers",
    ],
}

ROLE_KEYWORDS = [
    "engineer",
    "developer",
    "data",
    "machine learning",
    "ml",
    "platform",
    "backend",
    "frontend",
    "infrastructure",
    "security",
    "product",
    "design",
]

GARBAGE_MARKERS = [
    "{",
    "}",
    ";",
    "window",
    "function",
    "svg",
    "data-",
    "href=",
    "var ",
    "const ",
    "let ",
    "script",
    "cookie",
    "privacy",
    "subscribe",
    "login",
    "sign in",
    "learn more",
    "view all",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _compliance_block() -> dict[str, bool]:
    return {
        "login_used": False,
        "captcha_bypass_used": False,
        "public_pages_only": True,
    }


def _is_role_title(text: str) -> bool:
    cleaned = " ".join(text.split()).strip()
    if not (5 <= len(cleaned) <= 120):
        return False

    lowered = cleaned.lower()

    if any(marker in lowered for marker in GARBAGE_MARKERS):
        return False

    return any(keyword in lowered for keyword in ROLE_KEYWORDS)


def collect_roles(company_name: str, careers_url: str) -> dict[str, Any]:
    text_candidates: list[str] = []
    last_error: Exception | None = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for _ in range(3):
            try:
                page.goto(careers_url, wait_until="domcontentloaded", timeout=60_000)
                page.wait_for_timeout(5_000)
                text_candidates = page.locator("a, h1, h2, h3, h4, button").all_text_contents()
                if text_candidates:
                    break
            except Exception as exc:
                last_error = exc
                page.wait_for_timeout(2_000)

        browser.close()

    if not text_candidates:
        return {
            "company_name": company_name,
            "open_roles": 0,
            "role_change_60d": None,
            "titles": [],
            "source_url": careers_url,
            "collected_at": _now_iso(),
            "collector": "playwright_public_careers",
            "collector_error": str(last_error) if last_error else "No page text collected",
            "compliance": _compliance_block(),
        }

    titles: list[str] = []

    for raw_text in text_candidates:
        cleaned = " ".join(raw_text.split()).strip()
        if _is_role_title(cleaned):
            titles.append(cleaned)

    unique_titles = list(dict.fromkeys(titles))

    return {
        "company_name": company_name,
        "open_roles": len(unique_titles),
        "role_change_60d": None,
        "titles": unique_titles[:25],
        "source_url": careers_url,
        "collected_at": _now_iso(),
        "collector": "playwright_public_careers",
        "collector_error": None,
        "compliance": _compliance_block(),
    }


def main() -> None:
    RAW_JOB_POSTS_DIR.mkdir(parents=True, exist_ok=True)

    for company_name, careers_urls in COMPANY_CAREERS_URLS.items():
        slug = slugify_company_name(company_name)
        out_path = RAW_JOB_POSTS_DIR / f"{slug}.json"

        payload: dict[str, Any] | None = None
        errors: list[str] = []

        for careers_url in careers_urls:
            candidate = collect_roles(company_name, careers_url)

            if candidate.get("open_roles", 0) > 0 and not candidate.get("collector_error"):
                payload = candidate
                break

            if candidate.get("collector_error"):
                errors.append(f"{careers_url}: {candidate['collector_error']}")

            payload = candidate

        if payload is None:
            payload = {
                "company_name": company_name,
                "open_roles": 0,
                "role_change_60d": None,
                "titles": [],
                "source_url": careers_urls[0],
                "collected_at": _now_iso(),
                "collector": "playwright_public_careers",
                "collector_error": "; ".join(errors) or "No careers URLs attempted",
                "compliance": _compliance_block(),
            }

        payload["attempted_urls"] = careers_urls
        if errors and not payload.get("collector_error"):
            payload["non_selected_url_errors"] = errors

        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
