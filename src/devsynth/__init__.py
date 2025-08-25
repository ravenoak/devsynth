"""DevSynth package metadata and lightweight helpers.

The package previously imported logging helpers and application subpackages
eagerly.  This made ``import devsynth`` expensive and caused unwanted side
effects during test runs.  The module now exposes lightweight wrappers that
lazy‑load logging utilities on demand and provides an explicit initialization
helper for tests or applications that require certain subpackages to be loaded
ahead of time.
"""

from __future__ import annotations

# Version and metadata
__version__ = "0.1.0a1"

# Names that are re-exported lazily from :mod:`devsynth.logger`
_EXPORTED = {
    "DevSynthLogger",
    "set_request_context",
    "clear_request_context",
    "get_logger",
    "setup_logging",
}

__all__ = sorted(_EXPORTED | {"initialize_subpackages", "__version__"})


def __getattr__(name: str):
    """Dynamically import attributes from :mod:`devsynth.logger`.

    This keeps the package import light-weight while preserving the public API
    that previously lived at the package root.
    """

    if name in _EXPORTED:
        try:
            from . import logger as _logger  # Local import for lazy loading
        except ModuleNotFoundError:  # pragma: no cover - fallback for missing module
            from . import logging_setup as _logger

        value = getattr(_logger, name)
        globals()[name] = value  # Cache for future lookups
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def initialize_subpackages() -> None:
    """Explicitly import optional subpackages.

    Historically these imports happened eagerly at package import time.  Tests
    that rely on these side effects should call this helper instead.
    """

    import importlib
    import sys

    for module in ("devsynth.application", "devsynth.application.memory"):
        if module in sys.modules:
            continue
        try:  # pragma: no cover - best effort
            importlib.import_module(module)
        except Exception:  # pragma: no cover - ignore if unavailable
            pass
