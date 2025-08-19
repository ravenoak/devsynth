"""Check that tests include valid requirement identifiers.

Usage:
    python scripts/check_reqid.py [FILES...]
    python scripts/check_reqid.py --rev-range <range>

The script validates that each test function's docstring contains a
``ReqID`` field that is not ``N/A``. When ``--rev-range`` is supplied,
only tests changed within the given Git revision range are checked.
"""

from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List

REQID_PATTERN = re.compile(r"ReqID:\s*(?P<value>.+)")


def _gather_changed_tests(rev_range: str) -> List[str]:
    """Return test files changed in the given Git revision range."""
    diff = subprocess.check_output(["git", "diff", "--name-only", rev_range], text=True)
    return [
        f
        for f in diff.splitlines()
        if f.startswith("tests/") and f.endswith(".py") and Path(f).is_file()
    ]


def _iter_test_functions(path: Path) -> Iterable[ast.FunctionDef]:
    """Yield test function nodes from the given Python file."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - surface parsing errors
        raise RuntimeError(f"Failed to parse {path}: {exc}") from exc
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test"):
            yield node
        if isinstance(node, ast.AsyncFunctionDef) and node.name.startswith("test"):
            yield node


def check_file(path: Path) -> List[str]:
    """Return a list of ReqID violations for a single file."""
    errors: List[str] = []
    for node in _iter_test_functions(path):
        doc = ast.get_docstring(node)
        if not doc or "ReqID" not in doc:
            errors.append(f"{path}:{node.lineno} {node.name} missing ReqID")
            continue
        match = REQID_PATTERN.search(doc)
        if not match or match.group("value").strip() in {"N/A", "N\\A", "NA"}:
            errors.append(f"{path}:{node.lineno} {node.name} has invalid ReqID")
    return errors


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Ensure tests include ReqID and do not use N/A",
    )
    parser.add_argument("files", nargs="*", help="Test files to check")
    parser.add_argument(
        "--rev-range",
        help="Git revision range to locate changed tests (e.g., origin/main..HEAD)",
    )
    args = parser.parse_args(argv)

    files: List[str]
    if args.files:
        files = [f for f in args.files if f.startswith("tests/") and f.endswith(".py")]
    elif args.rev_range:
        files = _gather_changed_tests(args.rev_range)
    else:
        files = [str(p) for p in Path("tests").rglob("test_*.py")]

    if not files:
        return 0

    all_errors: List[str] = []
    for f in files:
        all_errors.extend(check_file(Path(f)))

    if all_errors:
        print("\n".join(all_errors), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - script entry
    sys.exit(main())
