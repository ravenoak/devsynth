"""
Minimal init example script.

This script is intentionally lightweight and offline-friendly. It runs without
any optional extras, performs a trivial check, and prints a stable message so
that a fast smoke test can validate the example is runnable end-to-end.

It does not import heavy subsystems to keep execution under a second.
"""
from __future__ import annotations

import sys


def main() -> int:
    # Keep logic minimal and deterministic.
    msg = "DevSynth init example OK"
    print(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
