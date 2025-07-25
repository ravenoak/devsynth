"""Audit logging utilities."""

from __future__ import annotations

import os
import logging
from devsynth.logging_setup import DevSynthLogger


_AUDIT_LOGGER = DevSynthLogger("devsynth.audit")


def audit_event(event: str, **details: object) -> None:
    """Log a security-related event for auditing purposes."""
    enabled = os.environ.get("DEVSYNTH_AUDIT_LOG_ENABLED", "1").lower() in {
        "1",
        "true",
        "yes",
    }
    if not enabled:
        return
    _AUDIT_LOGGER.info(event, **details)
