"""Deployment security hardening utilities.

This module provides lightweight helpers that enforce secure defaults
for runtime environments. These checks are intended to be called early
in application start-up to catch insecure deployment configurations.
"""

from __future__ import annotations

import os
from typing import Iterable

from .validation import parse_bool_env


def require_non_root_user() -> None:
    """Raise ``RuntimeError`` if running as root when non-root is required.

    The check is enabled when the ``DEVSYNTH_REQUIRE_NON_ROOT`` environment
    variable evaluates to ``true``. It is a no-op otherwise.
    """

    if not parse_bool_env("DEVSYNTH_REQUIRE_NON_ROOT", False):
        return
    # ``os.geteuid`` is not available on some platforms (e.g., Windows)
    geteuid = getattr(os, "geteuid", None)
    if callable(geteuid) and geteuid() == 0:
        raise RuntimeError("Running as root is not permitted")


def check_required_env_vars(names: Iterable[str]) -> None:
    """Ensure all required environment variables are present.

    Args:
        names: Iterable of environment variable names to validate.

    Raises:
        RuntimeError: If any variables are missing.
    """

    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        joined = ", ".join(sorted(missing))
        raise RuntimeError(f"Missing required environment variables: {joined}")


def apply_secure_umask(default: int = 0o077) -> int:
    """Set a restrictive umask for newly created files.

    Args:
        default: Mask to apply. Defaults to ``0o077`` which restricts access to
        the owner only.

    Returns:
        The previous umask value.
    """

    return os.umask(default)


def harden_runtime(required_env: Iterable[str] | None = None) -> None:
    """Apply basic deployment hardening checks.

    This helper can be called at program start-up to enforce non-root
    execution, verify required environment variables and apply a secure
    default ``umask``.
    """

    if required_env:
        check_required_env_vars(required_env)
    require_non_root_user()
    apply_secure_umask()
