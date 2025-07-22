from __future__ import annotations

"""Application-level unified configuration loader.

This module wraps :class:`devsynth.config.unified_loader.UnifiedConfigLoader`
with awareness of the ``DEVSYNTH_PROJECT_DIR`` environment variable.
"""

import os
from pathlib import Path
from typing import Optional

from devsynth.config.unified_loader import (
    UnifiedConfigLoader as _CoreLoader,
    UnifiedConfig,
)


class UnifiedConfigLoader:
    """Load and save project configuration respecting environment overrides."""

    @staticmethod
    def load(path: Optional[str | Path] = None) -> UnifiedConfig:
        project_dir = os.environ.get("DEVSYNTH_PROJECT_DIR")
        base = Path(path or project_dir or Path.cwd())
        return _CoreLoader.load(base)

    @staticmethod
    def save(config: UnifiedConfig) -> Path:
        return _CoreLoader.save(config)


__all__ = ["UnifiedConfigLoader"]
