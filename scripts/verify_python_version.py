#!/usr/bin/env python3
"""Check that Python version is at least 3.12."""
import sys

MIN_VERSION = (3, 12)

if sys.version_info < MIN_VERSION:
    sys.stderr.write(
        f"[error] Python {MIN_VERSION[0]}.{MIN_VERSION[1]} or higher is required; found {sys.version.split()[0]}\n"
    )
    raise SystemExit(1)

print(f"[info] Python {sys.version.split()[0]} detected")
