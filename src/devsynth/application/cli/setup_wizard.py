"""Interactive setup wizard used by ``devsynth init``."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from devsynth.config import ProjectUnifiedConfig, load_project_config
from devsynth.config.unified_loader import UnifiedConfigLoader
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge

from .progress import ProgressManager


def _env_flag(name: str) -> Optional[bool]:
    """Return boolean value for ``name`` if set, otherwise ``None``."""
    val = os.environ.get(name)
    if val is None:
        return None
    return val.lower() in {"1", "true", "yes"}


def _parse_features(value: Optional[Union[List[str], str]]) -> Dict[str, bool]:
    """Parse feature flags from list or JSON string."""
    if value is None or hasattr(value, "param_decls"):
        return {}
    if isinstance(value, list):
        if len(value) == 1:
            item = value[0]
            try:
                parsed = json.loads(item)
            except json.JSONDecodeError:
                return {item: True}
        else:
            return {f: True for f in value}
    else:
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {f.strip(): True for f in value.split(";") if f.strip()}

    if isinstance(parsed, dict):
        return {k: bool(v) for k, v in parsed.items()}
    if isinstance(parsed, list):
        return {f: True for f in parsed}
    return {}


class SetupWizard:
    """Guide the user through project initialization."""

    # Help text for each option
    HELP_TEXT = {
        "root": (
            "The root directory of your project. "
            "This is where DevSynth will store configuration files."
        ),
        "structure": (
            "Choose 'single_package' for a simple project with one main package, "
            "or 'monorepo' for a project with multiple packages."
        ),
        "language": (
            "The primary programming language for your project. "
            "This affects code generation and analysis."
        ),
        "constraints": (
            "Optional path to a file containing project constraints. "
            "These will guide the AI in generating code that meets your requirements."
        ),
        "goals": (
            "Optional description of your project goals. "
            "This helps the AI understand what you're trying to achieve."
        ),
        "memory_backend": (
            "The storage backend for DevSynth's memory system:\n"
            "- memory: In-memory storage (not persistent)\n"
            "- file: File-based storage\n"
            "- kuzu: Kuzu graph database\n"
            "- chromadb: ChromaDB vector database"
        ),
        "offline_mode": (
            "When enabled, DevSynth will use deterministic local providers "
            "instead of online LLM APIs."
        ),
        "features": {
            "wsde_collaboration": (
                "Enable collaboration between multiple AI agents using the WSDE model."
            ),
            "dialectical_reasoning": (
                "Enable dialectical reasoning for more robust decision making."
            ),
            "code_generation": "Enable automatic code generation from specifications.",
            "test_generation": "Enable automatic test generation from specifications.",
            "documentation_generation": (
                "Enable automatic documentation generation from code."
            ),
            "experimental_features": (
                "Enable experimental features that may not be fully stable."
            ),
        },
    }

    # Quick setup presets
    QUICK_SETUP_PRESETS = {
        "minimal": {
            "structure": "single_package",
            "memory_backend": "memory",
            "offline_mode": False,
            "features": {
                "wsde_collaboration": False,
                "dialectical_reasoning": False,
                "code_generation": True,
                "test_generation": True,
                "documentation_generation": True,
                "experimental_features": False,
            },
        },
        "standard": {
            "structure": "single_package",
            "memory_backend": "file",
            "offline_mode": False,
            "features": {
                "wsde_collaboration": True,
                "dialectical_reasoning": True,
                "code_generation": True,
                "test_generation": True,
                "documentation_generation": True,
                "experimental_features": False,
            },
        },
        "advanced": {
            "structure": "monorepo",
            "memory_backend": "chromadb",
            "offline_mode": False,
            "features": {
                "wsde_collaboration": True,
                "dialectical_reasoning": True,
                "code_generation": True,
                "test_generation": True,
                "documentation_generation": True,
                "experimental_features": True,
            },
        },
    }

    def __init__(self, bridge: Optional[UXBridge] = None) -> None:
        self.bridge = bridge or CLIUXBridge()
        self.console = Console()
        # Basic, Project, Memory, Features, Finalize
        self.total_steps = 5
        self.current_step = 0
        self.progress_manager = ProgressManager(self.bridge)
        self._progress_id = "wizard"

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _show_progress(self, description: str, status: str = None) -> None:
        """Advance the wizard progress indicator with an optional status."""
        self.current_step += 1
        desc = f"Step {self.current_step}/{self.total_steps}: {description}"
        self.progress_manager.update_progress(
            self._progress_id, advance=1, description=desc, status=status
        )
        self.bridge.display_result(f"[bold blue]{desc}[/bold blue]")

    def _show_help(self, topic: str, subtopic: Optional[str] = None) -> None:
        """Show help text for a specific option."""
        if subtopic:
            help_text = self.HELP_TEXT.get("features", {}).get(
                subtopic, "No help available"
            )
        else:
            help_text = self.HELP_TEXT.get(topic, "No help available")

        self.console.print(
            Panel(
                Markdown(help_text),
                title=f"Help: {topic.replace('_', ' ').title()}",
                border_style="blue",
            )
        )

    def _prompt_with_help(self, topic: str, question: str, **kwargs) -> Any:
        """Prompt the user with a question and offer help."""
        self._show_help(topic)
        return self.bridge.ask_question(question, **kwargs)

    def _prompt_features(
        self,
        cfg: ProjectUnifiedConfig,
        features: Optional[Dict[str, bool]],
        auto_confirm: bool,
    ) -> Dict[str, bool]:
        existing = cfg.config.features or {}
        result: Dict[str, bool] = {}
        features = features or {}

        self._show_progress("Configure Features", status="selection")
        self.bridge.display_result(
            "[italic]Configure which features to enable in your "
            "DevSynth project.[/italic]"
        )

        feature_list = [
            "wsde_collaboration",
            "dialectical_reasoning",
            "code_generation",
            "test_generation",
            "documentation_generation",
            "experimental_features",
        ]

        for feat in feature_list:
            if feat in features:
                result[feat] = bool(features[feat])
            elif auto_confirm:
                result[feat] = bool(existing.get(feat, False))
            else:
                self._show_help("features", feat)
                result[feat] = self.bridge.confirm_choice(
                    f"Enable {feat.replace('_', ' ')}?",
                    default=existing.get(feat, False),
                )
        return result

    def _apply_quick_setup(
        self, preset: str, cfg: ProjectUnifiedConfig
    ) -> Dict[str, Any]:
        """Apply a quick setup preset."""
        if preset not in self.QUICK_SETUP_PRESETS:
            self.bridge.display_result(
                f"[yellow]Unknown preset: {preset}. Using 'standard' instead.[/yellow]"
            )
            preset = "standard"

        preset_config = self.QUICK_SETUP_PRESETS[preset]

        return {
            "structure": preset_config["structure"],
            "memory_backend": preset_config["memory_backend"],
            "offline_mode": preset_config["offline_mode"],
            "features": preset_config["features"],
        }

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
        features: Optional[List[str]] = None,
        auto_confirm: Optional[bool] = None,
    ) -> ProjectUnifiedConfig:
        """Execute the wizard steps and persist configuration."""

        auto_confirm = (
            _env_flag("DEVSYNTH_AUTO_CONFIRM") if auto_confirm is None else auto_confirm
        )
        features = _parse_features(features)

        self.progress_manager.create_progress(
            self._progress_id, "Setup Wizard", total=self.total_steps
        )

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
            self.bridge.display_result(
                "[yellow]Project already initialized[/yellow]",
                message_type="warning",
            )
            self.progress_manager.complete_progress(self._progress_id)
            return cfg

        # Welcome message
        self.bridge.display_result(
            "[bold green]Welcome to the DevSynth Setup Wizard![/bold green]"
        )
        self.bridge.display_result(
            "[italic]This wizard will guide you through setting up your "
            "DevSynth project.[/italic]"
        )

        # Offer quick setup option
        quick_setup = False
        if not auto_confirm:
            quick_setup = self.bridge.confirm_choice(
                "Would you like to use quick setup with predefined configurations?",
                default=False,
            )

        quick_preset = None
        if quick_setup:
            quick_preset = self.bridge.ask_question(
                "Choose a configuration preset",
                choices=["minimal", "standard", "advanced"],
                default="standard",
            )
            preset_config = self._apply_quick_setup(quick_preset, cfg)
            structure = preset_config["structure"]
            memory_backend = preset_config["memory_backend"]
            offline_mode = preset_config["offline_mode"]
            features = preset_config["features"]

            # Still need to ask for these basic settings
            self._show_progress("Basic Settings", status="preset applied")
            # Mark remaining sections as satisfied by preset
            self._show_progress("Project Configuration", status="preset")
            self._show_progress("Memory Configuration", status="preset")
            self._show_progress("Feature Selection", status="preset")
        else:
            self._show_progress("Basic Settings", status="collecting")

        # Basic settings (always ask for these)
        root = root or os.environ.get("DEVSYNTH_INIT_ROOT")
        if root is None:
            root = self._prompt_with_help("root", "Project root", default=os.getcwd())

        language = language or os.environ.get("DEVSYNTH_INIT_LANGUAGE")
        if language is None:
            language = self._prompt_with_help(
                "language", "Primary language", default="python"
            )

        # Project settings
        if not quick_setup:
            self._show_progress("Project Configuration", status="collecting")

            structure = structure or os.environ.get("DEVSYNTH_INIT_STRUCTURE")
            if structure is None:
                structure = self._prompt_with_help(
                    "structure",
                    "Project structure",
                    choices=["single_package", "monorepo"],
                    default="single_package",
                )

            if constraints is None:
                constraints = os.environ.get("DEVSYNTH_INIT_CONSTRAINTS")
                if constraints is None:
                    constraints = (
                        self._prompt_with_help(
                            "constraints",
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
                        self._prompt_with_help(
                            "goals",
                            "Project goals (optional)",
                            default="",
                            show_default=False,
                        )
                        or None
                    )

            # Memory settings
            self._show_progress("Memory Configuration", status="configuring")

            memory_backend = memory_backend or os.environ.get(
                "DEVSYNTH_INIT_MEMORY_BACKEND"
            )
            if memory_backend is None:
                memory_backend = self._prompt_with_help(
                    "memory_backend",
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

            # Feature settings (progress handled within _prompt_features)
            features = self._prompt_features(cfg, features, auto_confirm)

        # Summary and confirmation
        self.bridge.display_result("\n[bold]Configuration Summary:[/bold]")
        self.bridge.display_result(f"Project Root: {root}")
        self.bridge.display_result(f"Language: {language}")
        self.bridge.display_result(f"Structure: {structure}")
        if constraints:
            self.bridge.display_result(f"Constraints: {constraints}")
        if goals:
            self.bridge.display_result(f"Goals: {goals}")
        self.bridge.display_result(f"Memory Backend: {memory_backend}")
        self.bridge.display_result(
            f"Offline Mode: {'Enabled' if offline_mode else 'Disabled'}"
        )

        self.bridge.display_result("\nFeatures:")
        for feat, enabled in features.items():
            self.bridge.display_result(
                f"  {feat.replace('_', ' ').title()}: "
                f"{'Enabled' if enabled else 'Disabled'}"
            )

        proceed = auto_confirm
        if not proceed:
            proceed = self.bridge.confirm_choice(
                "Proceed with initialization?", default=True
            )

        if not proceed:
            self.bridge.display_result(
                "[yellow]Initialization aborted.[/yellow]", message_type="warning"
            )
            self.progress_manager.complete_progress(self._progress_id)
            return cfg

        # Finalization step
        self._show_progress("Finalizing Setup", status="writing config")

        # Show progress during initialization
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("[green]Initializing project...", total=None)

            cfg.set_root(root)
            cfg.config.structure = structure
            cfg.set_language(language)
            cfg.set_goals(goals or "")
            cfg.config.constraints = constraints
            cfg.config.memory_store_type = memory_backend
            cfg.config.offline_mode = offline_mode
            cfg.config.features = features
            cfg.path = UnifiedConfigLoader.save(cfg)

            progress.update(
                task, description="[green]Project initialized successfully!"
            )

        self.progress_manager.complete_progress(self._progress_id)
        self.bridge.display_result(
            "[bold green]Initialization complete![/bold green]",
            highlight=True,
            message_type="success",
        )

        # Show next steps
        self.bridge.display_result("\n[bold]Next Steps:[/bold]")
        self.bridge.display_result(
            "1. Create or edit your requirements file: requirements.md"
        )
        self.bridge.display_result("2. Generate specifications: devsynth spec")
        self.bridge.display_result("3. Generate tests: devsynth test")
        self.bridge.display_result("4. Generate code: devsynth code")

        return cfg


__all__ = ["SetupWizard"]
