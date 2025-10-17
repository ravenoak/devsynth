import importlib.util
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol, TYPE_CHECKING, Any

from rich.console import Console

if TYPE_CHECKING:
    from devsynth.interface.ux_bridge import UXBridge
else:
    UXBridge = Any

# Lazy imports to improve CLI startup performance
def _get_cli_utils():
    from devsynth.application.cli.utils import _check_services
    return _check_services

def _get_config_loader():
    from devsynth.core.config_loader import _find_project_config, load_config
    return _find_project_config, load_config

def _get_interfaces():
    from devsynth.interface.cli import CLIUXBridge
    from devsynth.interface.ux_bridge import UXBridge
    return CLIUXBridge, UXBridge

def _get_logger():
    from devsynth.logging_setup import DevSynthLogger
    return DevSynthLogger(__name__)

# Lazy-loaded logger to avoid import-time overhead (not used in this module)
console = Console()


class DoctorBridge(Protocol):
    """Minimal bridge contract required by :func:`doctor_cmd`."""

    def print(
        self, message: str, *, highlight: bool = False, message_type: str | None = None
    ) -> None: ...


def _get_or_create_bridge(bridge: Optional[UXBridge] = None) -> DoctorBridge:
    """Get or create the CLI bridge, initializing lazily."""
    if bridge is not None:
        return bridge

    # Lazy initialization of default bridge
    if globals().get("bridge") is None:
        CLIUXBridge, UXBridge = _get_interfaces()
        globals()["bridge"] = CLIUXBridge()

    return globals()["bridge"]


@dataclass(slots=True)
class DoctorOptions:
    """Typed container for command options."""

    config_dir: Path
    quick: bool
    bridge: DoctorBridge


def doctor_cmd(
    config_dir: Path = Path("config"),
    quick: bool = False,
    *,
    bridge: Optional[UXBridge] = None,
) -> None:
    """Validate environment configuration files and provide hints.

    Parameters
    ----------
    config_dir:
        Directory containing environment configuration files.
    bridge:
        Optional :class:`UXBridge` instance used for output. If not
        provided, the module default CLI bridge is used.

    Example
    -------
    ``devsynth doctor --config-dir ./config``
    """
    # Lazy initialization of dependencies
    _check_services = _get_cli_utils()
    _find_project_config, load_config = _get_config_loader()

    # Lazy bridge initialization
    options_bridge = _get_or_create_bridge(bridge)

    options = DoctorOptions(
        config_dir=Path(config_dir),
        quick=quick,
        bridge=options_bridge,
    )
    try:
        config = load_config()
        _check_services(options.bridge)
        if _find_project_config(Path.cwd()) is None:
            options_bridge.print(
                "[yellow]No project configuration found. Run 'devsynth init' to create it.[/yellow]"
            )

        warnings = False
        critical_missing = False

        # verify expected directory structure
        required_dirs = ["src", "tests", "docs"]
        missing_dirs = [d for d in required_dirs if not (Path.cwd() / d).exists()]
        if missing_dirs:
            options_bridge.print(
                f"[yellow]Missing expected directories: {', '.join(missing_dirs)}[/yellow]"
            )
            warnings = True

        if sys.version_info < (3, 12):
            options_bridge.print(
                f"[yellow]Warning: Python 3.12 or higher is required. Current version: {sys.version.split()[0]}[/yellow]"
            )
            warnings = True

        # Check Poetry availability (recommended workflow)
        if shutil.which("poetry") is None:
            options_bridge.print(
                "[yellow]Poetry is not installed or not on PATH. Install Poetry for consistent dev workflows.[/yellow]"
            )
            warnings = True

        missing_keys = [
            key for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY") if not os.getenv(key)
        ]
        if missing_keys:
            options_bridge.print(
                f"[yellow]Missing environment variables: {', '.join(missing_keys)}[/yellow]"
            )
            warnings = True

        # check for core dependencies
        core_deps = ["rich", "pytest"]
        missing_deps = [
            pkg for pkg in core_deps if importlib.util.find_spec(pkg) is None
        ]
        if missing_deps:
            options_bridge.print(
                f"[yellow]Missing dependencies: {', '.join(missing_deps)}[/yellow]"
            )
            warnings = True

        # WebUI alignment check (Streamlit is the declared 0.1.0a1 webui extra)
        # This must not import streamlit; only check availability via find_spec.
        webui_spec = importlib.util.find_spec("streamlit")
        if webui_spec is None:
            options_bridge.print(
                "[yellow]WebUI alignment: Streamlit is not installed. If you intend to use the WebUI, install the 'webui' extra: `poetry install --with dev,docs --extras \"webui\"` or add it to your current env. See docs/developer_guides/testing.md.[/yellow]"
            )
            warnings = True

        # Warn when optional dependencies for enabled features are missing
        feature_pkgs = {
            "wsde_collaboration": "langgraph",
            "documentation_generation": "mkdocs",
            "test_generation": "pytest",
        }
        for feat, pkg in feature_pkgs.items():
            if (
                getattr(config, "features", {}).get(feat)
                and importlib.util.find_spec(pkg) is None
            ):
                options_bridge.print(
                    f"[yellow]Feature '{feat}' requires the '{pkg}' package which is not installed.[/yellow]"
                )
                warnings = True

        store_pkgs = {
            "chromadb": "chromadb",
            "kuzu": "kuzu",
            "faiss": "faiss",
            "tinydb": "tinydb",
        }
        store_type = str(getattr(config, "memory_store_type", "memory") or "memory")
        store_pkg: Optional[str] = store_pkgs.get(store_type)
        if store_pkg:
            if store_pkg == "faiss":
                spec = importlib.util.find_spec("faiss") or importlib.util.find_spec(
                    "faiss-cpu"
                )
            else:
                spec = importlib.util.find_spec(store_pkg)
            if spec is None:
                options_bridge.print(
                    f"[yellow]{store_type.capitalize()} support is enabled but the '{store_pkg}' package is missing.[/yellow]"
                )
                warnings = True
                critical_missing = True

        if importlib.util.find_spec("uvicorn") is None:
            options_bridge.print(
                "[yellow]The 'uvicorn' package is required for the API server but is not installed.[/yellow]"
            )
            warnings = True

        # Load validation utilities dynamically
        # Determine repository root (go up from src/devsynth/application/cli/commands)
        # parents[5] points to the project root (beyond 'src')
        repo_root = Path(__file__).resolve().parents[5]
        script_path = repo_root / "scripts" / "validate_config.py"
        spec = importlib.util.spec_from_file_location("validate_config", script_path)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        envs = ["default", "development", "testing", "staging", "production"]
        configs = {}

        for env in envs:
            cfg_path = options.config_dir / f"{env}.yml"
            if not cfg_path.exists():
                options_bridge.print(
                    f"[yellow]Warning: configuration file not found: {cfg_path}[/yellow]"
                )
                warnings = True
                continue

            data = module.load_config(str(cfg_path))
            configs[env] = data

            schema_errors = module.validate_config(data, module.CONFIG_SCHEMA)
            env_errors = module.validate_environment_variables(data)
            for err in schema_errors + env_errors:
                options_bridge.print(f"[yellow]{env}: {err}[/yellow]")
                warnings = True

        consistency_errors = module.check_config_consistency(configs)
        for err in consistency_errors:
            options_bridge.print(f"[yellow]{err}[/yellow]")
            warnings = True

        if options.quick:
            options_bridge.print("[blue]Running alignment check...[/blue]")
            try:
                from . import align_cmd

                issues = align_cmd.check_alignment(bridge=options_bridge)
                align_cmd.display_issues(issues, bridge=options_bridge)
                if issues:
                    warnings = True
            except Exception as exc:  # pragma: no cover - defensive
                options_bridge.print(
                    f"[yellow]Alignment check could not be run: {exc}[/yellow]"
                )
                warnings = True

            options_bridge.print("[blue]Running unit tests...[/blue]")
            try:
                from devsynth.testing.run_tests import run_tests

                success, _ = run_tests("unit-tests")
                if not success:
                    options_bridge.print("[yellow]Unit tests failed[/yellow]")
                    warnings = True
                else:
                    options_bridge.print("[green]Unit tests passed[/green]")
            except Exception as exc:  # pragma: no cover - defensive
                options_bridge.print(
                    f"[yellow]Unit tests could not be run: {exc}[/yellow]"
                )
                warnings = True

        if warnings:
            options_bridge.print(
                "[yellow]Configuration issues detected. Run 'devsynth init' to generate defaults.[/yellow]"
            )
        else:
            options_bridge.print("[green]All configuration files are valid.[/green]")

        if critical_missing:
            raise SystemExit(1)
    except Exception as err:  # pragma: no cover - defensive
        options_bridge.print(f"[red]Error:[/red] {err}", highlight=False)
