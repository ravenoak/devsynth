#!/usr/bin/env python3
"""
Verify that test functions contain a "ReqID:" tag in their docstrings.

Usage:
  python scripts/verify_docstring_reqids.py [--report] [--report-file PATH] [--path DIR]
  python scripts/verify_docstring_reqids.py --files test_a.py test_b.py  # limit to files (for pre-commit)

- --report: write a machine-readable JSON report with findings.
- --report-file: path to write report (default diagnostics/test_reqids_report.json if --report given).
- --path: directory to scan (default tests/).
- --files: optional explicit list of test files to scan; overrides --path when provided.

Exit codes:
  0: All good (no violations) or report-only mode with --report and no --strict.
  1: Violations found.
  2: Internal error / invalid arguments.

Notes:
- This script uses only stdlib to fit into minimal environments.
- It checks only test_*.py files and functions starting with "test_".
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def find_tests_missing_reqid_in_file(path: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        findings.append(
            {
                "file": str(path),
                "test": "<file_read_error>",
                "reason": f"Could not read file: {e}",
            }
        )
        return findings
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as e:
        findings.append(
            {"file": str(path), "test": "<syntax_error>", "reason": f"SyntaxError: {e}"}
        )
        return findings
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            doc = ast.get_docstring(node) or ""
            if "ReqID:" not in doc:
                findings.append(
                    {
                        "file": str(path),
                        "test": node.name,
                        "reason": "Missing 'ReqID:' in test function docstring",
                    }
                )
    return findings


def find_tests_missing_reqid(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path in root.rglob("test_*.py"):
        findings.extend(find_tests_missing_reqid_in_file(path))
    return findings


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="store_true", help="Write JSON report")
    parser.add_argument("--report-file", default=None, help="Report file path")
    parser.add_argument("--path", default="tests", help="Directory to scan")
    parser.add_argument(
        "--files", nargs="*", help="Optional explicit list of test files to scan"
    )
    args = parser.parse_args(argv)

    findings: list[dict[str, str]]
    scanned: list[str]

    if args.files:
        file_paths = [Path(p) for p in args.files if p.endswith(".py")]
        scanned = [str(p) for p in file_paths]
        findings = []
        for p in file_paths:
            # Only consider files under tests/ and named test_*.py
            if "tests" not in str(p) or not Path(p).name.startswith("test_"):
                continue
            findings.extend(find_tests_missing_reqid_in_file(Path(p)))
    else:
        root = Path(args.path)
        if not root.exists():
            print(f"[verify_reqids] path does not exist: {root}", file=sys.stderr)
            return 2
        findings = find_tests_missing_reqid(root)
        scanned = [str(root)]

    if args.report:
        out_path = Path(args.report_file or "diagnostics/test_reqids_report.json")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "scanned": scanned,
                    "missing_reqid_count": len(findings),
                    "findings": findings,
                },
                f,
                indent=2,
            )
        print(f"[verify_reqids] report written to {out_path}")

    if findings:
        print(
            f"[verify_reqids] FAIL: {len(findings)} test(s) missing 'ReqID:' docstring tag."
        )
        for item in findings[:10]:
            print(f" - {item['file']}::{item['test']}: {item['reason']}")
        return 1
    else:
        print("[verify_reqids] OK: All test functions contain 'ReqID:' tags.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
