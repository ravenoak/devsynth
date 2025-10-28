#!/usr/bin/env python3
"""
Basic secret scanning guard for CI and local runs.

Scans the repository for common high-risk secret patterns and fails if potential
secrets are found outside of approved placeholders and directories.

- Uses a conservative allowlist of placeholders (e.g., "test-openai-key").
- Skips typical binary/large or generated paths.
- Intended as a lightweight complement to Bandit/Safety.

Exit code 0 on success (no findings), 3 on findings, 0 with message if all matches
are allowlisted.

Usage:
  poetry run python scripts/check_no_secrets.py
"""
from __future__ import annotations

import os
import re
import sys
from collections.abc import Iterable

# Directories to skip entirely
SKIP_DIRS: set[str] = {
    ".git",
    ".venv",
    "venv",
    "build",
    "dist",
    "htmlcov",
    ".pytest_cache",
    "test_reports",
    "__pycache__",
    ".mypy_cache",
}

# Files or patterns to skip
SKIP_FILE_PATTERNS: Iterable[re.Pattern[str]] = (
    re.compile(r".*\.png$", re.I),
    re.compile(r".*\.jpg$", re.I),
    re.compile(r".*\.jpeg$", re.I),
    re.compile(r".*\.gif$", re.I),
    re.compile(r".*\.svg$", re.I),
    re.compile(r".*\.pdf$", re.I),
    re.compile(r".*\.lock$", re.I),
)

# Allowlist substrings that should not trip the scanner
ALLOWLIST_SUBSTRINGS: tuple[str, ...] = (
    "test-openai-key",
    "example-openai-key",
    "<YOUR-API-KEY>",
)

# Regexes for high-risk secret patterns
PATTERNS: Iterable[tuple[str, re.Pattern[str]]] = (
    (
        "OpenAI API key",
        re.compile(r"\bOPENAI_API_KEY\s*[:=]\s*['\"]?[A-Za-z0-9-_]{10,}\b"),
    ),
    ("AWS Access Key ID", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("AWS Secret Access Key", re.compile(r"\baws_secret_access_key\b\s*[:=]", re.I)),
    ("Private Key PEM", re.compile(r"-----BEGIN (RSA |DSA |EC )?PRIVATE KEY-----")),
    ("GitHub personal access token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("Slack token", re.compile(r"\bxox[abpr]-[A-Za-z0-9-]{10,}\b")),
)

# Scan only these top-level roots to reduce noise
ROOTS: tuple[str, ...] = ("src", "scripts", "docs", "examples", ".github")

# Skip patterns by path (regex)
SKIP_PATH_REGEXES: Iterable[re.Pattern[str]] = (re.compile(r"tests?/fixtures?/", re.I),)


def _should_skip_path(path: str) -> bool:
    if any(p in path.split(os.sep) for p in SKIP_DIRS):
        return True
    for rx in SKIP_FILE_PATTERNS:
        if rx.match(path):
            return True
    for rx in SKIP_PATH_REGEXES:
        if rx.search(path):
            return True
    return False


def main() -> int:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    findings: list[str] = []

    for root in ROOTS:
        abs_root = os.path.join(repo_root, root)
        if not os.path.exists(abs_root):
            continue
        for dirpath, dirnames, filenames in os.walk(abs_root):
            # In-place prune skip dirs for efficiency
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fname in filenames:
                path = os.path.join(dirpath, fname)
                rel_path = os.path.relpath(path, repo_root)
                if _should_skip_path(rel_path):
                    continue
                try:
                    with open(path, encoding="utf-8", errors="ignore") as f:
                        text = f.read()
                except Exception:
                    continue
                for label, rx in PATTERNS:
                    for m in rx.finditer(text):
                        snippet = text[max(0, m.start() - 20) : m.end() + 20]
                        if any(s in snippet for s in ALLOWLIST_SUBSTRINGS):
                            continue
                        findings.append(f"{rel_path}: {label} -> {m.group(0)[:60]}")

    if findings:
        print(
            "Potential secrets detected. Please remove or replace with env vars/secrets store and placeholders.\n"
        )
        for item in findings:
            print(f"- {item}")
        print(
            "\nIf these are false positives, add safe placeholders or extend ALLOWLIST_SUBSTRINGS with caution."
        )
        return 3

    print("Secret scan passed: no high-risk patterns found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
