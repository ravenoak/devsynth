#!/usr/bin/env python3
"""
verify_smoke_notice.py

Purpose:
  Help verify pytest smoke mode shows the plugin-autoload disabled notice.
  This supports acceptance task 1.6.2 in docs/tasks.md.

Behavior:
  - Reads input from a file path provided via --input, or from stdin if not provided.
  - Searches for phrases indicating plugin autoload is disabled.
  - Writes a short result file under test_reports/smoke_plugin_notice.txt with PASS/FAIL and the matched phrase (if any).
  - Exits 0 on success (notice found), 1 otherwise.

Usage examples:
  poetry run python scripts/verify_smoke_notice.py --input test_reports/collect_only_output.txt
  poetry run python scripts/verify_smoke_notice.py < test_reports/collect_only_output.txt

Notes:
  Keep outputs deterministic and under test_reports/ for CI artifact collection.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

NOTICE_PATTERNS = [
    # Common pytest message when plugin autoload is disabled
    r"PYTEST_DISABLE_PLUGIN_AUTOLOAD\s*=\s*1",
    r"plugin autoloading disabled",
    r"auto[- ]?loading of external plugins is disabled",
]


def detect_notice(text: str) -> str | None:
    for pat in NOTICE_PATTERNS:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(0)
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify pytest smoke plugin-disabled notice is present.")
    parser.add_argument("--input", type=str, default=None, help="Path to file containing pytest output. Reads stdin if omitted.")
    parser.add_argument("--out", type=str, default="test_reports/smoke_plugin_notice.txt", help="Where to write the result summary.")
    args = parser.parse_args(argv)

    if args.input:
        content = Path(args.input).read_text(encoding="utf-8", errors="ignore")
    else:
        content = sys.stdin.read()

    matched = detect_notice(content)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if matched:
        out_path.write_text(f"PASS: Detected smoke plugin-disabled notice: {matched}\n", encoding="utf-8")
        return 0
    else:
        out_path.write_text("FAIL: Smoke plugin-disabled notice not detected.\n", encoding="utf-8")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
