"""Initialize a new DevSynth project with streamlined prompts."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated, List, Optional

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
    defaults: Annotated[
        bool, typer.Option("--defaults", help="Use default values for all prompts")
    ] = False,
    non_interactive: Annotated[
        bool,
        typer.Option("--non-interactive", help="Run without interactive prompts"),
    ] = False,
    bridge: Optional[UXBridge] = None,
) -> None:
    """Initialize a new project with fewer interactive steps."""

    bridge = _resolve_bridge(bridge)
    auto_confirm = (
        (_env_flag("DEVSYNTH_AUTO_CONFIRM") if auto_confirm is None else auto_confirm)
        or defaults
        or non_interactive
    )

    def _ask(
        prompt: str,
        default: str,
        *,
        choices: Optional[List[str]] = None,
    ) -> str:
        """Prompt the user unless running in auto-confirm mode."""

        if auto_confirm:
            return default
        return bridge.ask_question(prompt, default=default, choices=choices)

    if non_interactive:
        os.environ["DEVSYNTH_NONINTERACTIVE"] = "1"

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
        root = root or _ask("Project root directory?", str(Path.cwd()))

        root_path = Path(root)
        if root_path.exists() and not root_path.is_dir():
            _handle_error(bridge, ValueError(f"'{root}' is not a directory"))
            return
        if not root_path.exists():
            try:
                root_path.mkdir(parents=True, exist_ok=True)
            except OSError as exc:  # pragma: no cover - defensive
                _handle_error(bridge, exc)
                return

        language = (
            language
            or os.environ.get("DEVSYNTH_INIT_LANGUAGE")
            or _ask("Primary language?", "python")
        )

        goals = goals or os.environ.get("DEVSYNTH_INIT_GOALS", "")
        if not goals:
            goals = _ask("Project goals?", "")

        memory_backend = memory_backend or os.environ.get(
            "DEVSYNTH_INIT_MEMORY_BACKEND"
        )
        memory_backend = memory_backend or _ask(
            "Select memory backend",
            "memory",
            choices=["memory", "file", "kuzu", "chromadb"],
        )

        valid_backends = {"memory", "file", "kuzu", "chromadb"}
        if memory_backend not in valid_backends:
            _handle_error(
                bridge, ValueError(f"Invalid memory backend: {memory_backend}")
            )
            return

        if offline_mode is None:
            env_offline = _env_flag("DEVSYNTH_INIT_OFFLINE_MODE")
            if env_offline is not None:
                offline_mode = env_offline
            elif auto_confirm:
                offline_mode = False
            else:
                offline_mode = bridge.confirm_choice(
                    "Enable offline mode?", default=False
                )

        try:
            env_feats = os.environ.get("DEVSYNTH_INIT_FEATURES")
            raw_features = features if features is not None else env_feats
            features_map = _parse_features(raw_features) if raw_features else {}
        except Exception as exc:
            _handle_error(bridge, exc)
            return

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
