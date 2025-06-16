from pathlib import Path
from rich.console import Console
from devsynth.logging_setup import DevSynthLogger
from devsynth.config.loader import load_config
import importlib.util

logger = DevSynthLogger(__name__)
console = Console()


def doctor_cmd(config_dir: str = "config") -> None:
    """Validate environment configuration files and provide hints.

    Example:
        `devsynth doctor --config-dir ./config`
    """
    try:
        # Ensure project configuration is present
        cfg_path_yaml = Path(".devsynth/devsynth.yml")
        cfg_path_toml = Path("pyproject.toml")
        if not cfg_path_yaml.exists() and not cfg_path_toml.exists():
            console.print(
                "[yellow]No project configuration found. Run 'devsynth init' to create it.[/yellow]"
            )

        # Load project configuration with the unified loader
        load_config()

        # Load validation utilities dynamically
        repo_root = Path(__file__).resolve().parents[4]
        script_path = repo_root / "scripts" / "validate_config.py"
        spec = importlib.util.spec_from_file_location("validate_config", script_path)
        module = importlib.util.module_from_spec(spec)  # type: ignore
        assert spec and spec.loader
        spec.loader.exec_module(module)  # type: ignore

        envs = ["default", "development", "testing", "staging", "production"]
        configs = {}
        warnings = False

        for env in envs:
            cfg_path = Path(config_dir) / f"{env}.yml"
            if not cfg_path.exists():
                console.print(f"[yellow]Warning: configuration file not found: {cfg_path}[/yellow]")
                warnings = True
                continue

            data = module.load_config(str(cfg_path))
            configs[env] = data

            schema_errors = module.validate_config(data, module.CONFIG_SCHEMA)
            env_errors = module.validate_environment_variables(data)
            for err in schema_errors + env_errors:
                console.print(f"[yellow]{env}: {err}[/yellow]")
                warnings = True

        consistency_errors = module.check_config_consistency(configs)
        for err in consistency_errors:
            console.print(f"[yellow]{err}[/yellow]")
            warnings = True

        if warnings:
            console.print(
                "[yellow]Configuration issues detected. Run 'devsynth init' to generate defaults.[/yellow]"
            )
        else:
            console.print("[green]All configuration files are valid.[/green]")
    except Exception as err:  # pragma: no cover - defensive
        console.print(f"[red]Error:[/red] {err}", highlight=False)
