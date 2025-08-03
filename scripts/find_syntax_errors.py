#!/usr/bin/env python3
"""Find syntax errors in Python files.

This script recursively scans a directory for ``.py`` files and reports
any syntax errors. The directory to scan may be provided as a positional
argument and defaults to the repository root.

Usage::

    python scripts/find_syntax_errors.py [DIRECTORY]
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(
        description="Recursively find syntax errors in Python files."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Directory to scan (default: repository root)",
    )
    return parser.parse_args()


def find_python_files(directory: Path) -> Iterable[Path]:
    """Yield Python files under ``directory`` recursively."""

    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    return (p for p in directory.rglob("*.py") if p.is_file())


def check_syntax(file_path: Path) -> Optional[str]:
    """Return an error message if ``file_path`` has a syntax error."""

    try:
        ast.parse(file_path.read_text(encoding="utf-8"))
    except SyntaxError as exc:  # pragma: no cover - exercised via tests
        return f"SyntaxError: {exc.msg} (line {exc.lineno}, column {exc.offset})"
    except Exception as exc:  # pragma: no cover - unexpected errors
        return f"Error: {exc}"
    return None


def main() -> int:
    """Script entry point."""

    args = parse_args()
    try:
        python_files = list(find_python_files(args.directory))
    except FileNotFoundError as exc:
        print(exc)
        return 1

    if not python_files:
        print("No Python files found")
        return 0

    errors: List[Tuple[Path, str]] = []
    for file_path in python_files:
        error = check_syntax(file_path)
        if error:
            errors.append((file_path, error))

    if errors:
        print(f"\nFound {len(errors)} files with syntax errors:")
        for path, error in errors:
            print(f"  {path}: {error}")
        return 1

    print("\nNo syntax errors found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
