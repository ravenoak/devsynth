#!/usr/bin/env python3
"""Verify security policy compliance by checking required environment variables.

The script enforces audit criteria defined in ``docs/policies/security.md``. It
ensures critical security controls are enabled before deployment and exits with
status ``1`` if any requirement is unmet.
"""
from __future__ import annotations

import os
from typing import List

REQUIRED_TRUE = [
    "DEVSYNTH_AUTHENTICATION_ENABLED",
    "DEVSYNTH_AUTHORIZATION_ENABLED",
    "DEVSYNTH_SANITIZATION_ENABLED",
    "DEVSYNTH_ENCRYPTION_AT_REST",
    "DEVSYNTH_ENCRYPTION_IN_TRANSIT",
    "DEVSYNTH_TLS_VERIFY",
    "DEVSYNTH_PRE_DEPLOY_APPROVED",
]

REQUIRED_NONEMPTY = ["DEVSYNTH_ACCESS_TOKEN"]


def main() -> int:
    """Check environment variables and report any violations."""
    failures: list[str] = []
    for name in REQUIRED_TRUE:
        if os.getenv(name, "").lower() != "true":
            failures.append(f"{name} must be set to 'true'")
    for name in REQUIRED_NONEMPTY:
        if not os.getenv(name):
            failures.append(f"{name} must be set")
    if failures:
        print("Security policy violations:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Security policy checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
