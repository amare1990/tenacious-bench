from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from enrichment.source_inventory import write_download_status_report


def main() -> None:
    report = write_download_status_report()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
