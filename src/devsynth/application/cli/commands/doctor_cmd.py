from pathlib import Path
from rich.console import Console
from devsynth.logging_setup import DevSynthLogger
from devsynth.core.config_loader import load_config, _find_project_config
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge
from typing import Optional
import importlib.util
import os
import sys

logger = DevSynthLogger(__name__)
bridge: UXBridge = CLIUXBridge()
console = Console()


def doctor_cmd(config_dir: str = "config", *, bridge: Optional[UXBridge] = None) -> None:
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
    ux_bridge = bridge if bridge is not None else globals()["bridge"]
    try:
        config = load_config()
        if _find_project_config(Path.cwd()) is None:
            ux_bridge.print(
                "[yellow]No project configuration found. Run 'devsynth init' to create it.[/yellow]"
            )

        warnings = False
        critical_missing = False

        if sys.version_info < (3, 11):
            ux_bridge.print(
                f"[yellow]Warning: Python 3.12 or higher is required. Current version: {sys.version.split()[0]}[/yellow]"
            )
            warnings = True

        missing_keys = [
            key for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY") if not os.getenv(key)
        ]
        if missing_keys:
            ux_bridge.print(
                f"[yellow]Missing environment variables: {', '.join(missing_keys)}[/yellow]"
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
                ux_bridge.print(
                    f"[yellow]Feature '{feat}' requires the '{pkg}' package which is not installed.[/yellow]"
                )
                warnings = True

        store_pkgs = {
            "chromadb": "chromadb",
            "kuzu": "kuzu",
            "faiss": "faiss",
            "tinydb": "tinydb",
        }
        store_type = getattr(config, "memory_store_type", "memory")
        pkg = store_pkgs.get(store_type)
        if pkg:
            if pkg == "faiss":
                spec = importlib.util.find_spec("faiss") or importlib.util.find_spec(
                    "faiss-cpu"
                )
            else:
                spec = importlib.util.find_spec(pkg)
            if spec is None:
                ux_bridge.print(
                    f"[yellow]{store_type.capitalize()} support is enabled but the '{pkg}' package is missing.[/yellow]"
                )
                warnings = True
                critical_missing = True

        if importlib.util.find_spec("uvicorn") is None:
            ux_bridge.print(
                "[yellow]The 'uvicorn' package is required for the API server but is not installed.[/yellow]"
            )
            warnings = True

        # Load validation utilities dynamically
        repo_root = Path(__file__).resolve().parents[4]
        script_path = repo_root / "scripts" / "validate_config.py"
        spec = importlib.util.spec_from_file_location("validate_config", script_path)
        module = importlib.util.module_from_spec(spec)  # type: ignore
        assert spec and spec.loader
        spec.loader.exec_module(module)  # type: ignore

        envs = ["default", "development", "testing", "staging", "production"]
        configs = {}

        for env in envs:
            cfg_path = Path(config_dir) / f"{env}.yml"
            if not cfg_path.exists():
                ux_bridge.print(
                    f"[yellow]Warning: configuration file not found: {cfg_path}[/yellow]"
                )
                warnings = True
                continue

            data = module.load_config(str(cfg_path))
            configs[env] = data

            schema_errors = module.validate_config(data, module.CONFIG_SCHEMA)
            env_errors = module.validate_environment_variables(data)
            for err in schema_errors + env_errors:
                ux_bridge.print(f"[yellow]{env}: {err}[/yellow]")
                warnings = True

        consistency_errors = module.check_config_consistency(configs)
        for err in consistency_errors:
            ux_bridge.print(f"[yellow]{err}[/yellow]")
            warnings = True

        if warnings:
            ux_bridge.print(
                "[yellow]Configuration issues detected. Run 'devsynth init' to generate defaults.[/yellow]"
            )
        else:
            ux_bridge.print("[green]All configuration files are valid.[/green]")

        if critical_missing:
            raise SystemExit(1)
    except Exception as err:  # pragma: no cover - defensive
        ux_bridge.print(f"[red]Error:[/red] {err}", highlight=False)
