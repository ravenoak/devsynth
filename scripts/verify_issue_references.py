#!/usr/bin/env python3
"""Verify that tests reference issues and requirement IDs in their docstrings.

This utility scans Python test files under ``tests/`` and ensures each test
function's docstring contains both an ``Issue: issues/<file>.md`` reference and a
``ReqID:`` token. The referenced issue file must exist relative to the project
root.

Usage:
    poetry run python scripts/verify_issue_references.py
    poetry run python scripts/verify_issue_references.py --json report.json
"""
from __future__ import annotations

import argparse
import ast
import json
import pathlib
import re
import sys

TEST_DIR = pathlib.Path("tests")
ISSUE_REGEX = re.compile(r"Issue:\s*(issues/[\w\-/]+\.md)")
REQID_REGEX = re.compile(r"ReqID:\s*([^\n]+)")


def is_test_function(node: ast.AST) -> bool:
    return isinstance(node, ast.FunctionDef) and node.name.startswith("test_")


def extract_docstring(node: ast.AST) -> str | None:
    return ast.get_docstring(node)


def file_has_opt_out(src: str, func_name: str) -> bool:
    pattern = re.compile(rf"def\s+{re.escape(func_name)}\s*\(.*\):.*#\s*no-issue-check")
    for line in src.splitlines():
        if pattern.search(line):
            return True
    return False


def scan_file(path: pathlib.Path) -> list[tuple[str, str]]:
    """Return list of (function_name, reason) for missing references."""
    try:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src)
    except Exception as e:  # pragma: no cover - syntax errors surfaced elsewhere
        return [("<file-parse>", f"Failed to parse {path}: {e}")]

    missing: list[tuple[str, str]] = []
    for node in tree.body:
        if is_test_function(node):
            if file_has_opt_out(src, node.name):
                continue
            doc = extract_docstring(node)
            if not doc:
                missing.append((node.name, "Missing docstring"))
                continue
            issue_match = ISSUE_REGEX.search(doc)
            reqid_match = REQID_REGEX.search(doc)
            if not issue_match:
                missing.append((node.name, "Missing Issue reference in docstring"))
            else:
                issue_path = pathlib.Path(issue_match.group(1))
                if not issue_path.exists():
                    missing.append(
                        (node.name, f"Issue path does not exist: {issue_path}")
                    )
            if not reqid_match:
                missing.append((node.name, "Missing ReqID in docstring"))
    return missing


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify that tests reference issues and ReqIDs in docstrings",
    )
    parser.add_argument(
        "--json",
        type=pathlib.Path,
        help="Optional JSON output report path",
    )
    args = parser.parse_args(argv)

    results: dict[str, list[tuple[str, str]]] = {}
    total_missing = 0

    if not TEST_DIR.exists():
        print("tests/ directory not found; nothing to verify.")
        return 0

    for path in TEST_DIR.rglob("test_*.py"):
        abs_path = path.resolve()
        rel = str(abs_path.relative_to(pathlib.Path.cwd()))
        missing = scan_file(abs_path)
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
        print("All tests include Issue references and ReqIDs. ✅")
        return 0

    print("Missing Issue/ReqID references detected:")
    for file, issues in results.items():
        print(f"- {file}")
        for func, reason in issues:
            print(f"    - {func}: {reason}")
    print(
        "\nPlease add both an Issue and ReqID reference to each test docstring, e.g.:\n"
        '    """Validate foo. Issue: issues/example.md ReqID: FR-01"""'
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
