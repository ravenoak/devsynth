"""Interactive setup wizard used by ``devsynth init``."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional


def _env_flag(name: str) -> Optional[bool]:
    """Return boolean value for ``name`` if set, otherwise ``None``."""
    val = os.environ.get(name)
    if val is None:
        return None
    return val.lower() in {"1", "true", "yes"}

from devsynth.config import load_project_config, ProjectUnifiedConfig
from devsynth.config.unified_loader import UnifiedConfigLoader
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge


class SetupWizard:
    """Guide the user through project initialization."""

    def __init__(self, bridge: Optional[UXBridge] = None) -> None:
        self.bridge = bridge or CLIUXBridge()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _prompt_features(
        self,
        cfg: ProjectUnifiedConfig,
        features: Optional[Dict[str, bool]],
        auto_confirm: bool,
    ) -> Dict[str, bool]:
        existing = cfg.config.features or {}
        result: Dict[str, bool] = {}
        features = features or {}
        for feat in [
            "wsde_collaboration",
            "dialectical_reasoning",
            "code_generation",
            "test_generation",
            "documentation_generation",
            "experimental_features",
        ]:
            if feat in features:
                result[feat] = bool(features[feat])
            elif auto_confirm:
                result[feat] = bool(existing.get(feat, False))
            else:
                result[feat] = self.bridge.confirm_choice(
                    f"Enable {feat.replace('_', ' ')}?",
                    default=existing.get(feat, False),
                )
        return result

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(
        self,
        *,
        root: Optional[str] = None,
        structure: Optional[str] = None,
        language: Optional[str] = None,
        constraints: Optional[str] = None,
        goals: Optional[str] = None,
        memory_backend: Optional[str] = None,
        offline_mode: Optional[bool] = None,
        features: Optional[Dict[str, bool]] = None,
        auto_confirm: Optional[bool] = None,
    ) -> ProjectUnifiedConfig:
        """Execute the wizard steps and persist configuration."""

        auto_confirm = _env_flag("DEVSYNTH_AUTO_CONFIRM") if auto_confirm is None else auto_confirm

        try:
            cfg = load_project_config()
        except Exception:
            from devsynth.config.loader import ConfigModel

            cfg = ProjectUnifiedConfig(
                ConfigModel(project_root=os.getcwd()),
                Path(os.getcwd()) / ".devsynth" / "project.yaml",
                False,
            )
        if cfg.exists():
            self.bridge.display_result("Project already initialized")
            return cfg

        root = root or os.environ.get("DEVSYNTH_INIT_ROOT")
        if root is None:
            root = self.bridge.ask_question("Project root", default=os.getcwd())

        structure = structure or os.environ.get("DEVSYNTH_INIT_STRUCTURE")
        if structure is None:
            structure = self.bridge.ask_question(
                "Project structure",
                choices=["single_package", "monorepo"],
                default="single_package",
            )

        language = language or os.environ.get("DEVSYNTH_INIT_LANGUAGE")
        if language is None:
            language = self.bridge.ask_question("Primary language", default="python")

        if constraints is None:
            constraints = os.environ.get("DEVSYNTH_INIT_CONSTRAINTS")
            if constraints is None:
                constraints = (
                    self.bridge.ask_question(
                        "Path to constraint file (optional)",
                        default="",
                        show_default=False,
                    )
                    or None
                )

        if goals is None:
            goals = os.environ.get("DEVSYNTH_INIT_GOALS")
            if goals is None:
                goals = (
                    self.bridge.ask_question(
                        "Project goals (optional)",
                        default="",
                        show_default=False,
                    )
                    or None
                )

        memory_backend = memory_backend or os.environ.get("DEVSYNTH_INIT_MEMORY_BACKEND")
        if memory_backend is None:
            memory_backend = self.bridge.ask_question(
                "Select memory backend",
                choices=["memory", "file", "kuzu", "chromadb"],
                default=cfg.config.memory_store_type,
            )

        if offline_mode is None:
            env_offline = _env_flag("DEVSYNTH_INIT_OFFLINE_MODE")
            if env_offline is not None:
                offline_mode = env_offline
            else:
                offline_mode = self.bridge.confirm_choice(
                    "Enable offline mode?", default=cfg.config.offline_mode
                )

        features = self._prompt_features(cfg, features, auto_confirm)

        proceed = auto_confirm
        if not proceed:
            proceed = self.bridge.confirm_choice("Proceed with initialization?", default=True)

        if not proceed:
            self.bridge.display_result("[yellow]Initialization aborted.[/yellow]")
            return cfg

        cfg.set_root(root)
        cfg.config.structure = structure
        cfg.set_language(language)
        cfg.set_goals(goals or "")
        cfg.config.constraints = constraints
        cfg.config.memory_store_type = memory_backend
        cfg.config.offline_mode = offline_mode
        cfg.config.features = features
        cfg.path = UnifiedConfigLoader.save(cfg)

        self.bridge.display_result("Initialization complete", highlight=True)
        return cfg


__all__ = ["SetupWizard"]
