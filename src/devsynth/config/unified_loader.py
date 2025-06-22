from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from .loader import ConfigModel, load_config, save_config, _find_config_path


@dataclass
class UnifiedConfig:
    """Wrapper around :class:`ConfigModel` with convenience helpers."""

    config: ConfigModel
    path: Path
    use_pyproject: bool

    def exists(self) -> bool:
        return self.path.exists()

    def set_root(self, root: str) -> None:
        self.config.project_root = root

    def set_language(self, language: str) -> None:
        self.config.language = language

    def set_goals(self, goals: str) -> None:
        self.config.goals = goals

    def save(self) -> Path:
        return save_config(
            self.config, self.use_pyproject, path=self.config.project_root
        )


class UnifiedConfigLoader:
    """Unified configuration loader used by the CLI."""

    @staticmethod
    def load(path: Optional[str | Path] = None) -> UnifiedConfig:
        root = Path(path or Path.cwd())
        cfg_path = _find_config_path(root)
        use_pyproject = False
        if cfg_path is not None and cfg_path.name == "pyproject.toml":
            use_pyproject = True
        else:
            cfg_path = root / ".devsynth" / "devsynth.yml"
        cfg = load_config(root)
        return UnifiedConfig(cfg, cfg_path, use_pyproject)
