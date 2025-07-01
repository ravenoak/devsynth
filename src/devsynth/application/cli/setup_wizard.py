"""Interactive setup wizard used by ``devsynth init``."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional

from devsynth.config import load_project_config, ProjectUnifiedConfig
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge


class SetupWizard:
    """Guide the user through project initialization."""

    def __init__(self, bridge: Optional[UXBridge] = None) -> None:
        self.bridge = bridge or CLIUXBridge()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _prompt_features(self, cfg: ProjectUnifiedConfig) -> Dict[str, bool]:
        features = cfg.config.features or {}
        for feat in [
            "wsde_collaboration",
            "dialectical_reasoning",
            "code_generation",
            "test_generation",
            "documentation_generation",
            "experimental_features",
        ]:
            features[feat] = self.bridge.confirm_choice(
                f"Enable {feat.replace('_', ' ')}?",
                default=features.get(feat, False),
            )
        return features

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self) -> ProjectUnifiedConfig:
        """Execute the wizard steps and persist configuration."""

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

        root = self.bridge.ask_question("Project root", default=os.getcwd())
        structure = self.bridge.ask_question(
            "Project structure",
            choices=["single_package", "monorepo"],
            default="single_package",
        )
        language = self.bridge.ask_question("Primary language", default="python")
        constraints = (
            self.bridge.ask_question(
                "Path to constraint file (optional)",
                default="",
                show_default=False,
            )
            or None
        )
        goals = (
            self.bridge.ask_question(
                "Project goals (optional)",
                default="",
                show_default=False,
            )
            or None
        )

        memory_backend = self.bridge.ask_question(
            "Select memory backend",
            choices=["memory", "file", "kuzu", "chromadb"],
            default=cfg.config.memory_store_type,
        )
        offline_mode = self.bridge.confirm_choice(
            "Enable offline mode?", default=cfg.config.offline_mode
        )

        features = self._prompt_features(cfg)

        if not self.bridge.confirm_choice("Proceed with initialization?", default=True):
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
        cfg.save()

        self.bridge.display_result("Initialization complete", highlight=True)
        return cfg


__all__ = ["SetupWizard"]
