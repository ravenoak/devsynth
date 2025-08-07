"""Initialize a new DevSynth project with streamlined prompts."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

import typer

from devsynth.config.loader import ConfigModel, _find_config_path, save_config
from devsynth.config.unified_loader import UnifiedConfigLoader
from devsynth.core.workflows import init_project
from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import DevSynthLogger

from ..utils import _env_flag, _handle_error, _parse_features, _resolve_bridge

logger = DevSynthLogger(__name__)


def init_cmd(
    wizard: bool = False,
    *,
    root: Optional[str] = None,
    language: Optional[str] = None,
    goals: Optional[str] = None,
    memory_backend: Optional[str] = None,
    offline_mode: Optional[bool] = None,
    features: Optional[List[str]] = typer.Option(
        None,
        help=(
            "Features to enable. Provide multiple --features options or a JSON mapping string."
        ),
    ),
    auto_confirm: Optional[bool] = None,
    bridge: Optional[UXBridge] = None,
) -> None:
    """Initialize a new project with fewer interactive steps."""

    bridge = _resolve_bridge(bridge)
    auto_confirm = (
        _env_flag("DEVSYNTH_AUTO_CONFIRM") if auto_confirm is None else auto_confirm
    )

    try:
        if wizard:
            from devsynth.application.cli.setup_wizard import SetupWizard

            SetupWizard(bridge).run()
            return

        if _find_config_path(Path.cwd()) is not None:
            bridge.display_result("[yellow]Project already initialized[/yellow]")
            return

        config = UnifiedConfigLoader.load().config

        root = root or os.environ.get("DEVSYNTH_INIT_ROOT")
        if root is None:
            root = bridge.ask_question(
                "Project root directory?", default=str(Path.cwd())
            )

        root_path = Path(root)
        if not root_path.exists():
            try:
                root_path.mkdir(parents=True, exist_ok=True)
            except OSError as exc:  # pragma: no cover - defensive
                bridge.display_result(
                    f"[red]Failed to create directory '{root}': {exc}[/red]",
                    message_type="error",
                )
                return

        language = language or os.environ.get("DEVSYNTH_INIT_LANGUAGE")
        if language is None:
            language = bridge.ask_question("Primary language?", default="python")

        goals = goals or os.environ.get("DEVSYNTH_INIT_GOALS", "")
        if not goals and not auto_confirm:
            goals = bridge.ask_question("Project goals?", default="")

        memory_backend = memory_backend or os.environ.get(
            "DEVSYNTH_INIT_MEMORY_BACKEND"
        )
        if memory_backend is None:
            memory_backend = bridge.ask_question(
                "Select memory backend",
                choices=["memory", "file", "kuzu", "chromadb"],
                default="memory",
            )
        if memory_backend not in {"memory", "file", "kuzu", "chromadb"}:
            bridge.display_result(
                f"[red]Invalid memory backend: {memory_backend}[/red]",
                message_type="error",
            )
            return

        if offline_mode is None:
            env_offline = _env_flag("DEVSYNTH_INIT_OFFLINE_MODE")
            if env_offline is not None:
                offline_mode = env_offline
            else:
                offline_mode = bridge.confirm_choice(
                    "Enable offline mode?", default=False
                )

        if features is None:
            env_feats = os.environ.get("DEVSYNTH_INIT_FEATURES")
            features_map = _parse_features(env_feats) if env_feats else {}
        else:
            features_map = _parse_features(features)

        config.project_root = root
        config.language = language
        config.goals = goals
        config.memory_store_type = memory_backend
        config.offline_mode = offline_mode
        config.features = features_map or {}

        try:
            save_config(
                ConfigModel(**config.as_dict()),
                use_pyproject=(Path("pyproject.toml").exists()),
            )
            init_project(
                root=root,
                structure=config.structure,
                language=language,
                goals=goals,
                memory_backend=memory_backend,
                offline_mode=offline_mode,
                features=features_map,
            )
            bridge.display_result(
                "[green]Initialization complete[/green]",
                highlight=True,
            )
        except Exception as save_err:  # pragma: no cover - defensive
            _handle_error(bridge, save_err)
    except Exception as err:  # pragma: no cover - defensive
        _handle_error(bridge, err)
