"""
Utilities for handling optional extras/backends with user-friendly guidance.

This module provides helpers that standardize error messages when optional
packages are missing. It aligns with the DevSynth guidelines for user-facing
UX polish and resilience by offering actionable next steps instead of raw
ImportError traces.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence


def _fmt_pkg_list(packages: Sequence[str]) -> str:
    return ", ".join(packages)


def suggest_install_message(
    *,
    extra_name: str | None,
    packages: Sequence[str],
    context: str,
) -> str:
    """
    Build a consistent, friendly message suggesting how to install missing extras.

    Args:
        extra_name: The extras group name from pyproject (e.g., "memory", "webui").
        packages: The underlying pip packages to install (e.g., ["chromadb"]).
        context: Short phrase describing what the user was trying to do.

    Returns:
        A user-friendly string with next-step guidance.
    """
    pkg_list = _fmt_pkg_list(list(packages))
    if extra_name:
        return (
            f"The following optional dependency is required for {context}: {pkg_list}.\n"
            f"Install via Poetry extras: 'poetry install --extras {extra_name}', or pip: \n"
            f"  pip install 'devsynth[{extra_name}]'\n"
            f"Alternatively, install packages directly:\n  pip install {pkg_list}"
        )
    else:
        return (
            f"The following optional dependency is required for {context}: {pkg_list}.\n"
            f"Install with: pip install {pkg_list}"
        )


def require_optional_package(
    import_error: ImportError,
    *,
    extra_name: str | None,
    packages: Sequence[str],
    context: str,
) -> ImportError:
    """
    Wrap an ImportError with a standardized, friendly guidance message.

    Usage:
        try:
            import chromadb  # type: ignore
        except ImportError as e:
            raise require_optional_package(e, extra_name="memory", packages=["chromadb"], context="ChromaDB memory store")

    Returns:
        An ImportError with an enhanced message preserving the original as cause.
    """
    message = suggest_install_message(
        extra_name=extra_name, packages=packages, context=context
    )
    e = ImportError(message)
    e.__cause__ = import_error
    return e
