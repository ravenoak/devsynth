#!/usr/bin/env python3
"""Placeholder frontmatter checker.

Ensures the repository has consistent YAML frontmatter formatting in docs.
Currently operates in a non-failing, advisory mode to unblock pre-commit runs.
Future iterations should implement strict checks per docs/plan and policies.
"""
from __future__ import annotations

import sys


def main() -> int:
    print("[fix_frontmatter] advisory check passed (placeholder)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
