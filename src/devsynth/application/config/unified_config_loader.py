from __future__ import annotations

"""Application-level unified configuration loader.

This module wraps :class:`devsynth.config.unified_loader.UnifiedConfigLoader`
with awareness of the ``DEVSYNTH_PROJECT_DIR`` environment variable.
"""

import os
from pathlib import Path
from typing import Optional, cast

from devsynth.config.unified_loader import (
    UnifiedConfig,
)
from devsynth.config.unified_loader import (
    UnifiedConfigLoader as CoreUnifiedConfigLoader,
)


class UnifiedConfigLoader:
    """Load and save project configuration respecting environment overrides."""

    @staticmethod
    def load(path: Optional[str | Path] = None) -> UnifiedConfig:
        project_dir = os.environ.get("DEVSYNTH_PROJECT_DIR")
        base = Path(path or project_dir or Path.cwd())
        return CoreUnifiedConfigLoader.load(base)

    @staticmethod
    def save(config: UnifiedConfig) -> Path:
        core_loader = CoreUnifiedConfigLoader()
        # NOTE(2026-02-15): mypy loses the staticmethod return type when the
        # application layer re-exports the loader; cast until the upstream
        # loader is exposed via a typed facade for reuse.
        return cast(Path, core_loader.save(config))


__all__ = ["UnifiedConfigLoader"]
