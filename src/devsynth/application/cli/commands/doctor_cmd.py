import importlib.util
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol

from rich.console import Console

from devsynth.application.cli.utils import _check_services
from devsynth.core.config_loader import _find_project_config, load_config
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
bridge: UXBridge = CLIUXBridge()
console = Console()


class DoctorBridge(Protocol):
    """Minimal bridge contract required by :func:`doctor_cmd`."""

    def print(
        self, message: str, *, highlight: bool = False, message_type: str | None = None
    ) -> None: ...


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
    options = DoctorOptions(
        config_dir=Path(config_dir),
        quick=quick,
        bridge=bridge if bridge is not None else globals()["bridge"],
    )
    try:
        config = load_config()
        _check_services(options.bridge)
        if _find_project_config(Path.cwd()) is None:
            options.bridge.print(
                "[yellow]No project configuration found. Run 'devsynth init' to create it.[/yellow]"
            )

        warnings = False
        critical_missing = False

        # verify expected directory structure
        required_dirs = ["src", "tests", "docs"]
        missing_dirs = [d for d in required_dirs if not (Path.cwd() / d).exists()]
        if missing_dirs:
            options.bridge.print(
                f"[yellow]Missing expected directories: {', '.join(missing_dirs)}[/yellow]"
            )
            warnings = True

        if sys.version_info < (3, 12):
            options.bridge.print(
                f"[yellow]Warning: Python 3.12 or higher is required. Current version: {sys.version.split()[0]}[/yellow]"
            )
            warnings = True

        # Check Poetry availability (recommended workflow)
        if shutil.which("poetry") is None:
            options.bridge.print(
                "[yellow]Poetry is not installed or not on PATH. Install Poetry for consistent dev workflows.[/yellow]"
            )
            warnings = True

        missing_keys = [
            key for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY") if not os.getenv(key)
        ]
        if missing_keys:
            options.bridge.print(
                f"[yellow]Missing environment variables: {', '.join(missing_keys)}[/yellow]"
            )
            warnings = True

        # check for core dependencies
        core_deps = ["rich", "pytest"]
        missing_deps = [
            pkg for pkg in core_deps if importlib.util.find_spec(pkg) is None
        ]
        if missing_deps:
            options.bridge.print(
                f"[yellow]Missing dependencies: {', '.join(missing_deps)}[/yellow]"
            )
            warnings = True

        # WebUI alignment check (Streamlit is the declared 0.1.0a1 webui extra)
        # This must not import streamlit; only check availability via find_spec.
        webui_spec = importlib.util.find_spec("streamlit")
        if webui_spec is None:
            options.bridge.print(
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
                options.bridge.print(
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
                options.bridge.print(
                    f"[yellow]{store_type.capitalize()} support is enabled but the '{store_pkg}' package is missing.[/yellow]"
                )
                warnings = True
                critical_missing = True

        if importlib.util.find_spec("uvicorn") is None:
            options.bridge.print(
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
                options.bridge.print(
                    f"[yellow]Warning: configuration file not found: {cfg_path}[/yellow]"
                )
                warnings = True
                continue

            data = module.load_config(str(cfg_path))
            configs[env] = data

            schema_errors = module.validate_config(data, module.CONFIG_SCHEMA)
            env_errors = module.validate_environment_variables(data)
            for err in schema_errors + env_errors:
                options.bridge.print(f"[yellow]{env}: {err}[/yellow]")
                warnings = True

        consistency_errors = module.check_config_consistency(configs)
        for err in consistency_errors:
            options.bridge.print(f"[yellow]{err}[/yellow]")
            warnings = True

        if options.quick:
            options.bridge.print("[blue]Running alignment check...[/blue]")
            try:
                from . import align_cmd

                issues = align_cmd.check_alignment(bridge=options.bridge)
                align_cmd.display_issues(issues, bridge=options.bridge)
                if issues:
                    warnings = True
            except Exception as exc:  # pragma: no cover - defensive
                options.bridge.print(
                    f"[yellow]Alignment check could not be run: {exc}[/yellow]"
                )
                warnings = True

            options.bridge.print("[blue]Running unit tests...[/blue]")
            try:
                from devsynth.testing.run_tests import run_tests

                success, _ = run_tests("unit-tests")
                if not success:
                    options.bridge.print("[yellow]Unit tests failed[/yellow]")
                    warnings = True
                else:
                    options.bridge.print("[green]Unit tests passed[/green]")
            except Exception as exc:  # pragma: no cover - defensive
                options.bridge.print(
                    f"[yellow]Unit tests could not be run: {exc}[/yellow]"
                )
                warnings = True

        if warnings:
            options.bridge.print(
                "[yellow]Configuration issues detected. Run 'devsynth init' to generate defaults.[/yellow]"
            )
        else:
            options.bridge.print("[green]All configuration files are valid.[/green]")

        if critical_missing:
            raise SystemExit(1)
    except Exception as err:  # pragma: no cover - defensive
        options.bridge.print(f"[red]Error:[/red] {err}", highlight=False)
