"""Configuration management commands."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from devsynth.config import config_key_autocomplete as loader_autocomplete
from devsynth.config.loader import ConfigModel, save_config
from devsynth.config.unified_loader import UnifiedConfigLoader
from devsynth.core import feature_flags, workflows
from devsynth.interface.ux_bridge import UXBridge

from ..utils import _handle_error, _resolve_bridge

config_app = typer.Typer(help="Manage configuration settings")


def config_key_autocomplete(ctx: typer.Context, incomplete: str):
    """Provide autocompletion for configuration keys."""

    return loader_autocomplete(ctx, incomplete)


@config_app.callback(invoke_without_command=True)
def config_cmd(
    key: str | None = typer.Option(None, autocompletion=config_key_autocomplete),
    value: str | None = None,
    list_models: bool = False,
    *,
    ctx: typer.Context | None = None,
    bridge: UXBridge | None = None,
) -> None:
    """View or set configuration options.

    This command allows you to view or modify DevSynth configuration settings.
    Without arguments, it displays all configuration settings.
    With a key, it displays the value for that key.
    With a key and value, it updates the configuration.

    Args:
        key: Configuration key to view or set
        value: Value to set for the specified key
        list_models: List available LLM models
        ctx: Typer context
        bridge: Optional UX bridge for interaction

    Examples:
        View all configuration settings:
        ```
        devsynth config
        ```

        View a specific configuration setting:
        ```
        devsynth config --key model
        ```

        Update a configuration setting:
        ```
        devsynth config --key model --value gpt-4
        ```

        List available LLM models:
        ```
        devsynth config --list-models
        ```
    """

    bridge = _resolve_bridge(bridge)

    # Handle Typer's OptionInfo objects
    if isinstance(key, typer.models.OptionInfo):
        key = None
    if isinstance(value, typer.models.OptionInfo):
        value = None

    # Skip if a subcommand is being invoked
    if ctx is not None and ctx.invoked_subcommand is not None:
        return

    try:
        # Load configuration
        config = UnifiedConfigLoader.load().config

        # Prepare arguments
        args = {"key": key, "value": value}
        if list_models:
            args["list_models"] = True

        # Execute command
        result = workflows.execute_command("config", args)

        # Handle result
        if result.get("success"):
            if key and value:
                # Update configuration
                try:
                    setattr(config, key, value)
                    save_config(
                        ConfigModel(**config.as_dict()),
                        use_pyproject=(Path("pyproject.toml").exists()),
                    )
                    bridge.display_result(
                        f"[green]Configuration updated: {key} = {value}[/green]"
                    )
                except Exception as save_err:
                    _handle_error(bridge, save_err)
            elif key:
                # Display specific configuration value
                bridge.display_result(f"[blue]{key}:[/blue] {result.get('value')}")
            elif list_models:
                # Display available models
                bridge.display_result(f"[blue]Available LLM Models:[/blue]")
                for model in result.get("models", []):
                    bridge.display_result(f"  [yellow]{model}[/yellow]")
            else:
                # Display all configuration settings
                bridge.display_result(f"[blue]DevSynth Configuration:[/blue]")
                for k, v in result.get("config", {}).items():
                    bridge.display_result(f"  [yellow]{k}:[/yellow] {v}")
        else:
            _handle_error(bridge, result)
    except Exception as err:  # pragma: no cover - defensive
        _handle_error(bridge, err)


@config_app.command("enable-feature")
def enable_feature_cmd(name: str, *, bridge: UXBridge | None = None) -> None:
    """Enable a feature flag in the project configuration.

    Example:
        `devsynth config enable-feature code_generation`
    """

    bridge = _resolve_bridge(bridge)
    try:
        config = UnifiedConfigLoader.load().config
        features = config.features or {}
        features[name] = True
        config.features = features
        save_config(
            ConfigModel(**config.as_dict()),
            use_pyproject=(Path("pyproject.toml").exists()),
        )

        feature_flags.refresh()
        bridge.display_result(f"Feature '{name}' enabled.")
    except Exception as err:
        bridge.display_result(f"[red]Error:[/red] {err}", highlight=False)


__all__ = ["config_app", "config_cmd", "enable_feature_cmd"]
