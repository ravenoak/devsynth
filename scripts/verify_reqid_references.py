#!/usr/bin/env python3
"""
Verify that tests include requirement IDs (ReqID) in their docstrings.

This script scans Python test files under ./tests and checks that each test
function has a docstring containing a requirement identifier in the form:

    ReqID: <ID>

Where <ID> is a non-empty token (e.g., FR-09, NFR-SEC-01, BUG-1234, etc.).

Notes:
- Skips auto-generated or sentinel tests if they explicitly contain
  '# no-reqid-check' on the test function line.
- Reports a summary and exits non-zero if any violations are found.

Usage:
    poetry run python scripts/verify_reqid_references.py
    poetry run python scripts/verify_reqid_references.py --json report.json

This tool supports the stabilization task: "Ensure tests include ReqID references
in docstrings (see tests/README)" and complements scripts/verify_requirements_traceability.py.
"""
from __future__ import annotations

import argparse
import ast
import json
import pathlib
import re
import sys
from typing import Dict, List, Tuple

TEST_DIR = pathlib.Path("tests")
REQID_REGEX = re.compile(r"ReqID:\s*([^\n]+)")


def is_test_function(node: ast.AST) -> bool:
    return isinstance(node, ast.FunctionDef) and node.name.startswith("test_")


def extract_docstring(node: ast.AST) -> str | None:
    return ast.get_docstring(node)


def file_has_opt_out(src: str, func_name: str) -> bool:
    pattern = re.compile(rf"def\s+{re.escape(func_name)}\s*\(.*\):.*#\s*no-reqid-check")
    # We only need to check lines; keep it simple
    for line in src.splitlines():
        if pattern.search(line):
            return True
    return False


def scan_file(path: pathlib.Path) -> list[tuple[str, str]]:
    """Return a list of (function_name, reason) for missing ReqID docstrings."""
    try:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src)
    except Exception as e:
        return [("<file-parse>", f"Failed to parse {path}: {e}")]

    missing: list[tuple[str, str]] = []
    for node in tree.body:
        if is_test_function(node):
            if file_has_opt_out(src, node.name):
                continue
            doc = extract_docstring(node)
            if not doc or REQID_REGEX.search(doc) is None:
                missing.append((node.name, "Missing or invalid ReqID in docstring"))
    return missing


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify that tests include ReqID in docstrings"
    )
    parser.add_argument(
        "--json",
        type=pathlib.Path,
        help="Optional JSON output report path",
        default=None,
    )
    args = parser.parse_args(argv)

    results: dict[str, list[tuple[str, str]]] = {}
    total_missing = 0

    if not TEST_DIR.exists():
        print("tests/ directory not found; nothing to verify.")
        return 0

    for path in TEST_DIR.rglob("test_*.py"):
        rel = str(path.relative_to(pathlib.Path.cwd()))
        missing = scan_file(path)
        if missing:
            results[rel] = missing
            total_missing += len(missing)

    if args.json:
        payload = {
            "total_missing": total_missing,
            "files": {
                k: [{"function": f, "reason": r} for f, r in v]
                for k, v in results.items()
            },
        }
        args.json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote JSON report to {args.json}")

    if total_missing == 0:
        print("All tests include ReqID references in docstrings. ✅")
        return 0

    print("Missing ReqID references detected:")
    for file, issues in results.items():
        print(f"- {file}")
        for func, reason in issues:
            print(f"    - {func}: {reason}")

    print(
        "\nPlease add a docstring to each test with a requirement reference, e.g.:\n"
        '    """Validate foo behavior. ReqID: FR-09"""\n'
        "To opt out for a specific test (discouraged), append '# no-reqid-check' to the def line."
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
