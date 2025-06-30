from pathlib import Path
from rich.console import Console
from devsynth.logging_setup import DevSynthLogger
from devsynth.core.config_loader import load_config, _find_project_config
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge
import importlib.util
import os
import sys

logger = DevSynthLogger(__name__)
bridge: UXBridge = CLIUXBridge()
console = Console()


def doctor_cmd(config_dir: str = "config") -> None:
    """Validate environment configuration files and provide hints.

    Example:
        `devsynth doctor --config-dir ./config`
    """
    try:
        config = load_config()
        if _find_project_config(Path.cwd()) is None:
            bridge.print(
                "[yellow]No project configuration found. Run 'devsynth init' to create it.[/yellow]"
            )

        warnings = False

        if sys.version_info < (3, 11):
            bridge.print(
                f"[yellow]Warning: Python 3.11 or higher is required. Current version: {sys.version.split()[0]}[/yellow]"
            )
            warnings = True

        missing_keys = [
            key for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY") if not os.getenv(key)
        ]
        if missing_keys:
            bridge.print(
                f"[yellow]Missing environment variables: {', '.join(missing_keys)}[/yellow]"
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
                bridge.print(
                    f"[yellow]Warning: configuration file not found: {cfg_path}[/yellow]"
                )
                warnings = True
                continue

            data = module.load_config(str(cfg_path))
            configs[env] = data

            schema_errors = module.validate_config(data, module.CONFIG_SCHEMA)
            env_errors = module.validate_environment_variables(data)
            for err in schema_errors + env_errors:
                bridge.print(f"[yellow]{env}: {err}[/yellow]")
                warnings = True

        consistency_errors = module.check_config_consistency(configs)
        for err in consistency_errors:
            bridge.print(f"[yellow]{err}[/yellow]")
            warnings = True

        if warnings:
            bridge.print(
                "[yellow]Configuration issues detected. Run 'devsynth init' to generate defaults.[/yellow]"
            )
        else:
            bridge.print("[green]All configuration files are valid.[/green]")
    except Exception as err:  # pragma: no cover - defensive
        bridge.print(f"[red]Error:[/red] {err}", highlight=False)
