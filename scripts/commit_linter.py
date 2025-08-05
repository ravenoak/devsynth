#!/usr/bin/env python3
"""Deprecated commit message linter script.

Use ``devsynth mvu lint`` instead of this script.
"""

from __future__ import annotations

from devsynth.core.mvu.linter import main


if __name__ == "__main__":  # pragma: no cover - thin wrapper
    raise SystemExit(main())
