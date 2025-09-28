"""DevSynth package metadata and lightweight helpers.

The package previously imported logging helpers and application subpackages
eagerly.  This made ``import devsynth`` expensive and caused unwanted side
effects during test runs.  The module now exposes lightweight wrappers that
lazy‑load logging utilities on demand and provides an explicit initialization
helper for tests or applications that require certain subpackages to be loaded
ahead of time.
"""

from __future__ import annotations

import importlib
import logging
import types
from typing import Any

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


def __getattr__(name: str) -> Any:
    """Dynamically import attributes from :mod:`devsynth.logger`.

    This keeps the package import light-weight while preserving the public API
    that previously lived at the package root.
    """

    if name in _EXPORTED:
        try:
            _log_mod = importlib.import_module(f"{__name__}.logger")
        except ModuleNotFoundError:  # pragma: no cover - fallback for missing module
            _log_mod = importlib.import_module(f"{__name__}.logging_setup")

        value = getattr(_log_mod, name)
        globals()[name] = value  # Cache for future lookups
        return value

    # Fallback: try to resolve unknown attributes as subpackages/modules
    try:
        module = importlib.import_module(f"{__name__}.{name}")
    except ModuleNotFoundError as exc:
        module = _maybe_create_config_stub(name, exc)
    except Exception as exc:  # pragma: no cover - defensive logging
        logging.getLogger(__name__).warning(
            "Error importing devsynth.%s: %s",
            name,
            exc,
        )
        module = None
    else:
        globals()[name] = module  # Cache the loaded submodule on the package
        return module

    if module is not None:
        globals()[name] = module
        return module

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def initialize_subpackages() -> None:
    """Explicitly import optional subpackages.

    Historically these imports happened eagerly at package import time.  Tests
    that rely on these side effects should call this helper instead.
    """

    import sys

    for module in ("devsynth.application", "devsynth.application.memory"):
        if module in sys.modules:
            continue
        try:  # pragma: no cover - best effort
            importlib.import_module(module)
        except ModuleNotFoundError:  # pragma: no cover - optional
            logging.getLogger(__name__).debug(
                "Optional subpackage %s not available", module
            )
        except Exception as exc:  # pragma: no cover - defensive
            logging.getLogger(__name__).warning(
                "Error importing optional subpackage %s: %s",
                module,
                exc,
            )


def _maybe_create_config_stub(name: str, exc: ModuleNotFoundError) -> Any:
    """Return a lightweight ``devsynth.config`` stub when dependencies are missing."""

    if name != "config":
        return None

    logger = logging.getLogger(__name__)
    logger.debug("Creating lightweight devsynth.config stub due to: %s", exc)

    settings_module = types.ModuleType("devsynth.config.settings")

    def _ensure_path_exists(*_args: object, **_kwargs: object) -> None:
        return None

    settings_module.ensure_path_exists = _ensure_path_exists  # type: ignore[attr-defined]

    class _Settings:
        enable_chromadb = False
        vector_store_enabled = False
        memory_store_type = "chromadb"
        provider_type = ""
        openai_api_key = ""
        lm_studio_endpoint = ""

    def _get_settings() -> _Settings:
        return _Settings()

    config_module = types.ModuleType("devsynth.config")
    config_module.settings = settings_module  # type: ignore[attr-defined]
    config_module.get_settings = _get_settings  # type: ignore[attr-defined]
    config_module.get_llm_settings = lambda: {}  # type: ignore[attr-defined]

    import sys

    sys.modules.setdefault("devsynth.config.settings", settings_module)
    sys.modules.setdefault("devsynth.config", config_module)

    return config_module
