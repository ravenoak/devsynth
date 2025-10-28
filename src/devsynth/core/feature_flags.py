from __future__ import annotations

"""Helpers for querying feature flags.

This module centralizes access to feature flag checks. Feature flags are
defined in the project configuration and may be toggled via the DevSynth CLI.
"""

from functools import lru_cache
from typing import Dict

from devsynth.config.loader import load_config


@lru_cache(maxsize=1)
def _feature_map() -> dict[str, bool]:
    """Return the feature flag mapping from configuration.

    The configuration is loaded lazily and cached for future lookups. Use
    :func:`refresh` after modifying configuration to ensure subsequent calls
    reflect the latest values.
    """

    cfg = load_config()
    return cfg.features or {}


def is_enabled(name: str) -> bool:
    """Return ``True`` if the named feature flag is enabled."""

    return bool(_feature_map().get(name, False))


def experimental_enabled() -> bool:
    """Convenience wrapper for the ``experimental_features`` flag."""

    return is_enabled("experimental_features")


def refresh() -> None:
    """Clear cached feature flags.

    Call this after persisting configuration changes so that future checks use
    updated values.
    """

    _feature_map.cache_clear()
