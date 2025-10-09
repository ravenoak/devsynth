"""Interactive setup wizard used by ``devsynth init``."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Any,
    Dict,
    Literal,
    Mapping,
    Optional,
    Protocol,
    Sequence,
    TypedDict,
    Union,
)

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from devsynth.config import ProjectUnifiedConfig, load_project_config
from devsynth.config.unified_loader import UnifiedConfigLoader
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import ProgressIndicator, UXBridge

from .progress import ProgressManager


def _env_flag(name: str) -> Optional[bool]:
    """Return boolean value for ``name`` if set, otherwise ``None``."""
    val = os.environ.get(name)
    if val is None:
        return None
    return val.lower() in {"1", "true", "yes"}


FeatureFlags = TypedDict(
    "FeatureFlags",
    {
        "wsde_collaboration": bool,
        "dialectical_reasoning": bool,
        "code_generation": bool,
        "test_generation": bool,
        "documentation_generation": bool,
        "experimental_features": bool,
    },
    total=False,
)


FeatureName = Literal[
    "wsde_collaboration",
    "dialectical_reasoning",
    "code_generation",
    "test_generation",
    "documentation_generation",
    "experimental_features",
]


FEATURE_NAMES: tuple[FeatureName, ...] = (
    "wsde_collaboration",
    "dialectical_reasoning",
    "code_generation",
    "test_generation",
    "documentation_generation",
    "experimental_features",
)


def _normalize_feature_flags(mapping: Mapping[str, object]) -> FeatureFlags:
    normalized: FeatureFlags = {}
    for name in FEATURE_NAMES:
        if name in mapping:
            normalized[name] = bool(mapping[name])
    return normalized


FeatureInput = Union[Mapping[str, object], Sequence[str], str, None]


def _parse_features(value: FeatureInput) -> FeatureFlags:
    """Parse feature flags from various representations into a mapping."""

    if value is None or hasattr(value, "param_decls"):
        return {}

    raw_flags: Dict[str, bool]

    if isinstance(value, Mapping):
        raw_flags = {k: bool(v) for k, v in value.items() if isinstance(k, str)}
    elif isinstance(value, Sequence) and not isinstance(value, str):
        if len(value) == 1:
            item = value[0]
            try:
                parsed = json.loads(item)
            except (TypeError, json.JSONDecodeError):
                raw_flags = {str(item): True}
            else:
                return _parse_features(parsed)
        else:
            raw_flags = {str(f): True for f in value}
    else:
        try:
            parsed = json.loads(value)
        except (TypeError, json.JSONDecodeError):
            raw_flags = {
                f.strip(): True for f in str(value).split(";") if f and f.strip()
            }
        else:
            return _parse_features(parsed)

    return _normalize_feature_flags(raw_flags)


@dataclass(frozen=True)
class QuickSetupPreset:
    """Immutable representation of quick setup defaults."""

    structure: str
    memory_backend: str
    offline_mode: bool
    features: Mapping[str, bool]

    def as_feature_flags(self) -> FeatureFlags:
        """Return a mutable mapping suitable for configuration updates."""

        return _normalize_feature_flags(self.features)


@dataclass(slots=True)
class WizardSelections:
    """Collects choices made during the setup wizard."""

    root: Path
    language: str
    structure: str
    constraints: Optional[Path]
    goals: Optional[str]
    memory_backend: str
    offline_mode: bool
    features: FeatureFlags


class WizardBridge(Protocol):
    """Protocol documenting the UX hooks used by :class:`SetupWizard`."""

    def ask_question(
        self,
        message: str,
        *,
        choices: Optional[Sequence[str]] = None,
        default: Optional[str] = None,
        show_default: bool = True,
    ) -> str: ...

    def confirm_choice(self, message: str, *, default: bool = False) -> bool: ...

    def display_result(
        self, message: str, *, highlight: bool = False, message_type: str | None = None
    ) -> None: ...

    def create_progress(
        self, description: str, *, total: int = 100
    ) -> ProgressIndicator: ...


class SetupWizard:
    """Guide the user through project initialization."""

    # Help text for each option
    HELP_TEXT: Dict[str, str | Dict[str, str]] = {
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

    QUICK_SETUP_PRESETS: Dict[str, QuickSetupPreset] = {
        "minimal": QuickSetupPreset(
            structure="single_package",
            memory_backend="memory",
            offline_mode=False,
            features={
                "wsde_collaboration": False,
                "dialectical_reasoning": False,
                "code_generation": True,
                "test_generation": True,
                "documentation_generation": True,
                "experimental_features": False,
            },
        ),
        "standard": QuickSetupPreset(
            structure="single_package",
            memory_backend="file",
            offline_mode=False,
            features={
                "wsde_collaboration": True,
                "dialectical_reasoning": True,
                "code_generation": True,
                "test_generation": True,
                "documentation_generation": True,
                "experimental_features": False,
            },
        ),
        "advanced": QuickSetupPreset(
            structure="monorepo",
            memory_backend="chromadb",
            offline_mode=False,
            features={
                "wsde_collaboration": True,
                "dialectical_reasoning": True,
                "code_generation": True,
                "test_generation": True,
                "documentation_generation": True,
                "experimental_features": True,
            },
        ),
    }

    def __init__(self, bridge: Optional[WizardBridge | UXBridge] = None) -> None:
        self.bridge: WizardBridge = bridge or CLIUXBridge()
        self.console = Console()
        # Basic, Project, Memory, Features, Finalize
        self.total_steps = 5
        self.current_step = 0
        self.progress_manager = ProgressManager(self.bridge)
        self._progress_id = "wizard"

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _show_progress(self, description: str, status: Optional[str] = None) -> None:
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
            features_help = self.HELP_TEXT.get("features")
            if isinstance(features_help, dict):
                help_text = features_help.get(subtopic, "No help available")
            else:
                help_text = "No help available"
        else:
            entry = self.HELP_TEXT.get(topic)
            help_text = entry if isinstance(entry, str) else "No help available"

        self.console.print(
            Panel(
                Markdown(help_text),
                title=f"Help: {topic.replace('_', ' ').title()}",
                border_style="blue",
            )
        )

    def _prompt_with_help(self, topic: str, question: str, **kwargs: Any) -> str:
        """Prompt the user with a question and offer help."""
        self._show_help(topic)
        return self.bridge.ask_question(question, **kwargs)

    def _prompt_features(
        self,
        cfg: ProjectUnifiedConfig,
        features: Optional[FeatureFlags],
        auto_confirm: bool,
    ) -> FeatureFlags:
        existing: Mapping[str, bool] = cfg.config.features or {}
        raw_flags: Dict[str, bool] = {}
        features = features or {}

        self._show_progress("Configure Features", status="selection")
        self.bridge.display_result(
            "[italic]Configure which features to enable in your "
            "DevSynth project.[/italic]"
        )

        feature_list: tuple[FeatureName, ...] = FEATURE_NAMES

        for feat in feature_list:
            if feat in features:
                raw_flags[feat] = bool(features[feat])
            elif auto_confirm:
                raw_flags[feat] = bool(existing.get(feat, False))
            else:
                self._show_help("features", feat)
                raw_flags[feat] = self.bridge.confirm_choice(
                    f"Enable {feat.replace('_', ' ')}?",
                    default=existing.get(feat, False),
                )
        return _normalize_feature_flags(raw_flags)

    def _apply_quick_setup(
        self, preset: str, cfg: ProjectUnifiedConfig
    ) -> QuickSetupPreset:
        """Apply a quick setup preset."""
        if preset not in self.QUICK_SETUP_PRESETS:
            self.bridge.display_result(
                f"[yellow]Unknown preset: {preset}. Using 'standard' instead.[/yellow]"
            )
            preset = "standard"

        preset_config = self.QUICK_SETUP_PRESETS[preset]
        return QuickSetupPreset(
            structure=preset_config.structure,
            memory_backend=preset_config.memory_backend,
            offline_mode=preset_config.offline_mode,
            features=dict(preset_config.features),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(
        self,
        *,
        root: Path | str | None = None,
        structure: Optional[str] = None,
        language: Optional[str] = None,
        constraints: Path | str | None = None,
        goals: Optional[str] = None,
        memory_backend: Optional[str] = None,
        offline_mode: Optional[bool] = None,
        features: FeatureInput = None,
        auto_confirm: Optional[bool] = None,
    ) -> ProjectUnifiedConfig:
        """Execute the wizard steps and persist configuration."""

        auto_confirm_flag = (
            _env_flag("DEVSYNTH_AUTO_CONFIRM") if auto_confirm is None else auto_confirm
        )
        feature_flags = _parse_features(features)

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

        self.bridge.display_result(
            "[bold green]Welcome to the DevSynth Setup Wizard![/bold green]"
        )
        self.bridge.display_result(
            "[italic]This wizard will guide you through setting up your "
            "DevSynth project.[/italic]"
        )

        def _ensure_path(value: Path | str | None) -> Optional[Path]:
            if value is None:
                return None
            if isinstance(value, Path):
                return value
            text = value.strip()
            return Path(text) if text else None

        root_path = _ensure_path(root or os.environ.get("DEVSYNTH_INIT_ROOT"))
        language_value = language or os.environ.get("DEVSYNTH_INIT_LANGUAGE")
        structure_value = structure or os.environ.get("DEVSYNTH_INIT_STRUCTURE")
        constraints_value: Path | str | None = constraints or os.environ.get(
            "DEVSYNTH_INIT_CONSTRAINTS"
        )
        goals_value = goals or os.environ.get("DEVSYNTH_INIT_GOALS")
        memory_backend_value = memory_backend or os.environ.get(
            "DEVSYNTH_INIT_MEMORY_BACKEND"
        )
        offline_mode_value = offline_mode

        quick_setup = False
        preset_config: Optional[QuickSetupPreset] = None
        if not auto_confirm_flag:
            quick_setup = self.bridge.confirm_choice(
                "Would you like to use quick setup with predefined configurations?",
                default=False,
            )

        if quick_setup:
            preset_choice = self.bridge.ask_question(
                "Choose a configuration preset",
                choices=["minimal", "standard", "advanced"],
                default="standard",
            )
            preset_config = self._apply_quick_setup(preset_choice, cfg)
            structure_value = preset_config.structure
            memory_backend_value = preset_config.memory_backend
            offline_mode_value = preset_config.offline_mode
            feature_flags = preset_config.as_feature_flags()
            self._show_progress("Basic Settings", status="preset applied")
            self._show_progress("Project Configuration", status="preset")
            self._show_progress("Memory Configuration", status="preset")
            self._show_progress("Feature Selection", status="preset")
        else:
            self._show_progress("Basic Settings", status="collecting")

        if root_path is None:
            root_path = Path(
                self._prompt_with_help("root", "Project root", default=os.getcwd())
            )

        if language_value is None:
            language_value = self._prompt_with_help(
                "language", "Primary language", default="python"
            )

        if not quick_setup:
            self._show_progress("Project Configuration", status="collecting")

            if structure_value is None:
                structure_value = self._prompt_with_help(
                    "structure",
                    "Project structure",
                    choices=["single_package", "monorepo"],
                    default="single_package",
                )

            if constraints_value is None:
                constraints_prompt = self._prompt_with_help(
                    "constraints",
                    "Path to constraint file (optional)",
                    default="",
                    show_default=False,
                )
                constraints_value = constraints_prompt or None

            if goals_value is None:
                goals_prompt = self._prompt_with_help(
                    "goals",
                    "Project goals (optional)",
                    default="",
                    show_default=False,
                )
                goals_value = goals_prompt or None

            self._show_progress("Memory Configuration", status="configuring")

            if memory_backend_value is None:
                memory_backend_value = self._prompt_with_help(
                    "memory_backend",
                    "Select memory backend",
                    choices=["memory", "file", "kuzu", "chromadb"],
                    default=cfg.config.memory_store_type,
                )

            if offline_mode_value is None:
                env_offline = _env_flag("DEVSYNTH_INIT_OFFLINE_MODE")
                if env_offline is not None:
                    offline_mode_value = env_offline
                else:
                    offline_mode_value = self.bridge.confirm_choice(
                        "Enable offline mode?", default=cfg.config.offline_mode
                    )

            feature_flags = self._prompt_features(
                cfg, feature_flags, bool(auto_confirm_flag)
            )

        constraints_path = _ensure_path(constraints_value)
        goals_text = goals_value or None
        memory_backend_value = memory_backend_value or cfg.config.memory_store_type
        offline_mode_value = (
            offline_mode_value
            if offline_mode_value is not None
            else cfg.config.offline_mode
        )
        language_value = language_value or "python"
        structure_value = structure_value or "single_package"

        selections = WizardSelections(
            root=root_path,
            language=language_value,
            structure=structure_value,
            constraints=constraints_path,
            goals=goals_text,
            memory_backend=memory_backend_value,
            offline_mode=offline_mode_value,
            features=feature_flags,
        )

        self.bridge.display_result("\n[bold]Configuration Summary:[/bold]")
        self.bridge.display_result(f"Project Root: {selections.root}")
        self.bridge.display_result(f"Language: {selections.language}")
        self.bridge.display_result(f"Structure: {selections.structure}")
        if selections.constraints:
            self.bridge.display_result(f"Constraints: {selections.constraints}")
        if selections.goals:
            self.bridge.display_result(f"Goals: {selections.goals}")
        self.bridge.display_result(f"Memory Backend: {selections.memory_backend}")
        self.bridge.display_result(
            "Offline Mode: " f"{'Enabled' if selections.offline_mode else 'Disabled'}"
        )

        self.bridge.display_result("\nFeatures:")
        for feat, enabled in selections.features.items():
            self.bridge.display_result(
                f"  {feat.replace('_', ' ').title()}: "
                f"{'Enabled' if enabled else 'Disabled'}"
            )

        proceed = bool(auto_confirm_flag)
        if not proceed:
            proceed = self.bridge.confirm_choice(
                "Proceed with initialization?", default=True
            )

        if not proceed:
            self.bridge.display_result(
                "[yellow]Initialization aborted.[/yellow]",
                message_type="warning",
            )
            self.progress_manager.complete_progress(self._progress_id)
            return cfg

        self._show_progress("Finalizing Setup", status="writing config")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("[green]Initializing project...", total=None)

            cfg.set_root(str(selections.root))
            cfg.config.structure = selections.structure
            cfg.set_language(selections.language)
            cfg.set_goals(selections.goals or "")
            cfg.config.constraints = (
                str(selections.constraints)
                if selections.constraints is not None
                else None
            )
            cfg.config.memory_store_type = selections.memory_backend
            cfg.config.offline_mode = selections.offline_mode
            cfg.config.features = dict(selections.features)
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

        self.bridge.display_result("\n[bold]Next Steps:[/bold]")
        self.bridge.display_result(
            "1. Create or edit your requirements file: requirements.md"
        )
        self.bridge.display_result("2. Generate specifications: devsynth spec")
        self.bridge.display_result("3. Generate tests: devsynth test")
        self.bridge.display_result("4. Generate code: devsynth code")

        return cfg


__all__ = ["SetupWizard"]
