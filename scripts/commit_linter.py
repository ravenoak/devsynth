#!/usr/bin/env python3
"""Deprecated commit message linter script.

Use ``devsynth mvu lint`` instead of this script.
"""

from __future__ import annotations

from devsynth.core.feature_flags import mvuu_enforcement_enabled
from devsynth.core.mvu.linter import main as linter_main


def main() -> int:
    """Run the MVUU commit message linter if enforcement is enabled."""

    if not mvuu_enforcement_enabled():
        return 0
    return linter_main()


if __name__ == "__main__":  # pragma: no cover - thin wrapper
    raise SystemExit(main())
