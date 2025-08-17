#!/usr/bin/env python3
"""Scan configs and source code for basic security policy violations.

The script searches for hardcoded secrets and debug flags in common configuration
and Python files. It exits with status ``1`` if any violations are detected.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable, List, Tuple

FORBIDDEN_PATTERNS = {
    re.compile(r"password\s*=", re.IGNORECASE): "Hardcoded password",
    re.compile(r"secret[_-]?key\s*=", re.IGNORECASE): "Hardcoded secret",
    re.compile(r"api[_-]?key\s*=", re.IGNORECASE): "Hardcoded API key",
    re.compile(r"access[_-]?token\s*=", re.IGNORECASE): "Hardcoded access token",
    re.compile(r"debug\s*=\s*true", re.IGNORECASE): "Debug enabled",
}

SCAN_EXTENSIONS = {".py", ".yaml", ".yml", ".env", ".ini", ".cfg"}


def scan_file(path: Path) -> List[Tuple[int, str, str]]:
    """Return a list of violations found in a single file."""
    try:
        text = path.read_text()
    except UnicodeDecodeError:
        return []
    violations: List[Tuple[int, str, str]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for pattern, message in FORBIDDEN_PATTERNS.items():
            if pattern.search(line):
                violations.append((lineno, line.strip(), message))
    return violations


def audit(paths: Iterable[Path]) -> List[Tuple[Path, int, str, str]]:
    """Scan provided paths for policy violations."""
    results: List[Tuple[Path, int, str, str]] = []
    for target in paths:
        if target.is_dir():
            for file in target.rglob("*"):
                if file.is_file() and file.suffix in SCAN_EXTENSIONS:
                    for lineno, snippet, message in scan_file(file):
                        results.append((file, lineno, snippet, message))
        elif target.is_file() and target.suffix in SCAN_EXTENSIONS:
            for lineno, snippet, message in scan_file(target):
                results.append((target, lineno, snippet, message))
    return results


def main(argv: List[str] | None = None) -> int:
    """CLI entry point for policy audit."""
    parser = argparse.ArgumentParser(
        description="Scan for policy violations in configuration and source files."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path.cwd()],
        help="Paths to scan (default: repository root)",
    )
    args = parser.parse_args(argv)
    findings = audit(args.paths)
    if findings:
        print("Policy violations found:")
        for file, lineno, snippet, message in findings:
            print(f"{file}:{lineno}: {message}: {snippet}")
        return 1
    print("No policy violations found.")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
