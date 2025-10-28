from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import toml  # type: ignore[import-untyped]  # TODO(2025-12-20): Adopt typed tomllib or bundle stubs.

from .loader import ConfigModel, _find_config_path, load_config, save_config


@dataclass
class UnifiedConfig:
    """Wrapper around :class:`ConfigModel` with convenience helpers."""

    config: ConfigModel
    path: Path
    use_pyproject: bool

    def exists(self) -> bool:
        if self.use_pyproject:
            if not self.path.exists():
                return False
            try:
                data = toml.load(self.path)
            except (OSError, toml.TomlDecodeError):
                return False
            return "devsynth" in data.get("tool", {})
        return self.path.exists()

    def set_root(self, root: str) -> None:
        self.config.project_root = root

    def set_language(self, language: str) -> None:
        self.config.language = language

    def set_goals(self, goals: str) -> None:
        self.config.goals = goals

    def set_kuzu_embedded(self, embedded: bool) -> None:
        """Enable or disable the embedded Kuzu backend."""
        self.config.kuzu_embedded = embedded

    def save(self) -> Path:
        return save_config(
            self.config, self.use_pyproject, path=self.config.project_root
        )


class UnifiedConfigLoader:
    """Unified configuration loader used by the CLI."""

    @staticmethod
    def load(path: str | Path | None = None) -> UnifiedConfig:
        root = Path(path or Path.cwd())
        cfg_path = _find_config_path(root)
        use_pyproject = False
        if cfg_path is not None:
            if cfg_path.name == "pyproject.toml":
                use_pyproject = True
        else:
            cfg_path = root / ".devsynth" / "project.yaml"

        cfg = load_config(root)
        return UnifiedConfig(cfg, cfg_path, use_pyproject)

    @staticmethod
    def save(config: UnifiedConfig) -> Path:
        """Persist a :class:`UnifiedConfig` to disk."""
        return save_config(
            config.config,
            config.use_pyproject,
            path=config.config.project_root,
        )
