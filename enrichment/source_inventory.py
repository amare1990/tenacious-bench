from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from briefs.models import RawSourceStatus


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"


EXPECTED_RAW_SOURCES = {
    "crunchbase_csv": RAW_DIR / "crunchbase" / "crunchbase-companies-information.csv",
    "crunchbase_json": RAW_DIR / "crunchbase" / "crunchbase_companies.json",
    "layoffs_csv": RAW_DIR / "layoffs" / "layoffs.csv",
    "job_posts_snapshot": RAW_DIR / "job_posts",
    "press_snapshot": RAW_DIR / "press",
    "tech_stack_snapshot": RAW_DIR / "tech_stack",
}


PLACEHOLDER_PATTERNS = ("<company_slug>", "placeholder")


def slugify_company_name(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower())
    return slug.strip("-") or "company"


def json_load(path: Path, default: Any) -> Any:
    if not path.exists() or path.stat().st_size == 0:
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
        f.write("\n")


def _directory_populated(path: Path) -> tuple[bool, str | None]:
    if not path.exists():
        return False, "directory missing"

    files = [p for p in path.iterdir() if p.is_file()]
    if not files:
        return False, "directory exists but contains no files"

    real_files = [
        p for p in files
        if p.name not in {".gitkeep", ".gitignore"}
        and not any(token in p.name for token in PLACEHOLDER_PATTERNS)
        and p.stat().st_size > 0
    ]
    if real_files:
        return True, None
    return False, "only placeholder files are present"


def build_raw_source_inventory() -> list[RawSourceStatus]:
    inventory: list[RawSourceStatus] = []

    for source_name, path in EXPECTED_RAW_SOURCES.items():
        if path.is_dir():
            populated, note = _directory_populated(path)
            inventory.append(
                RawSourceStatus(
                    source_name=source_name,
                    path=str(path.relative_to(DATA_DIR.parent)),
                    present=path.exists(),
                    populated=populated,
                    notes=note,
                )
            )
            continue

        present = path.exists()
        populated = present and path.stat().st_size > 0
        note = None
        if present and not populated:
            note = "file exists but is empty"
        elif not present:
            note = "file missing"

        inventory.append(
            RawSourceStatus(
                source_name=source_name,
                path=str(path.relative_to(DATA_DIR.parent)),
                present=present,
                populated=populated,
                notes=note,
            )
        )

    return inventory


def write_download_status_report() -> dict[str, Any]:
    inventory = build_raw_source_inventory()
    missing_or_empty = [item.model_dump() for item in inventory if not item.populated]
    report = {
        "inventory": [item.model_dump() for item in inventory],
        "missing_or_empty": missing_or_empty,
    }
    json_dump(RAW_DIR / "download_status.json", report)
    return report
