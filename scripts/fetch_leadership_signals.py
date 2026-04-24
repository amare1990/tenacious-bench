from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from enrichment.source_inventory import slugify_company_name

RAW_PRESS_DIR = Path("data/raw/press")

COMPANY_PRESS_URLS = {
    "Ramp": "https://ramp.com/blog",
    "Clay": "https://www.clay.com/blog",
    "Retool": "https://retool.com/blog",
}

KEYWORDS = [
    "cto",
    "chief technology officer",
    "vp engineering",
    "vice president engineering",
    "head of engineering",
    "engineering leader",
    "engineering leadership",
]


def collect_press(company_name: str, url: str) -> list[dict]:
    try:
        response = httpx.get(
            url,
            timeout=30.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        response.raise_for_status()
    except Exception as exc:
        return [
            {
                "title": "Leadership collector error",
                "published_at": datetime.now(timezone.utc).isoformat(),
                "summary": str(exc),
                "source_url": url,
                "collector": "public_press_http",
                "collector_error": str(exc),
            }
        ]

    soup = BeautifulSoup(response.text, "html.parser")
    results: list[dict] = []

    for tag in soup.find_all(["h1", "h2", "h3", "a", "p"]):
        text = " ".join(tag.get_text(" ", strip=True).split())
        if not text:
            continue

        lowered = text.lower()
        if any(keyword in lowered for keyword in KEYWORDS):
            results.append(
                {
                    "title": text[:250],
                    "published_at": datetime.now(timezone.utc).isoformat(),
                    "summary": text[:500],
                    "source_url": url,
                    "collector": "public_press_http",
                }
            )

    deduped: list[dict] = []
    seen: set[str] = set()

    for item in results:
        key = item["title"].lower()
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    if not deduped:
        return [
            {
                "title": "No leadership change signal found",
                "published_at": datetime.now(timezone.utc).isoformat(),
                "summary": f"No leadership keyword match found on public press page for {company_name}.",
                "source_url": url,
                "collector": "public_press_http",
                "collector_error": None,
            }
        ]

    return deduped[:10]


def main() -> None:
    RAW_PRESS_DIR.mkdir(parents=True, exist_ok=True)

    for company_name, url in COMPANY_PRESS_URLS.items():
        slug = slugify_company_name(company_name)
        out_path = RAW_PRESS_DIR / f"{slug}.json"
        payload = collect_press(company_name, url)
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
