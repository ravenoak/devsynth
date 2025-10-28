"""Deployment security hardening utilities.

This module provides lightweight helpers that enforce secure defaults
for runtime environments. These checks are intended to be called early
in application start-up to catch insecure deployment configurations.
"""

from __future__ import annotations

import os
from collections.abc import Iterable

from .validation import parse_bool_env


def require_non_root_user() -> None:
    """Raise ``RuntimeError`` if running as root when non-root is required."""

    if (
        parse_bool_env("DEVSYNTH_REQUIRE_NON_ROOT", False)
        and getattr(os, "geteuid", lambda: 1)() == 0
    ):
        raise RuntimeError("Running as root is not permitted")  # pragma: no cover


def check_required_env_vars(names: Iterable[str]) -> None:
    """Ensure all required environment variables are present."""

    missing = [name for name in names if not os.environ.get(name)]  # pragma: no cover
    if missing:  # pragma: no cover
        raise RuntimeError(  # pragma: no cover
            "Missing required environment variables: " + ", ".join(sorted(missing))
        )


def apply_secure_umask(default: int = 0o077) -> int:
    """Set a restrictive umask for newly created files.

    Args:
        default: Mask to apply. Defaults to ``0o077`` which restricts access to
        the owner only.

    Returns:
        The previous umask value.
    """

    return os.umask(default)  # pragma: no cover


def harden_runtime(required_env: Iterable[str] | None = None) -> None:
    """Apply basic deployment hardening checks.

    This helper can be called at program start-up to enforce non-root
    execution, verify required environment variables and apply a secure
    default ``umask``.
    """

    if required_env:  # pragma: no cover
        check_required_env_vars(required_env)  # pragma: no cover
    require_non_root_user()  # pragma: no cover
    apply_secure_umask()  # pragma: no cover
