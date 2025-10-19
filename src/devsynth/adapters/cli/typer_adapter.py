import importlib
import os
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click
import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from typer import completion as typer_completion

# Ensure CLI commands are registered before using the registry
import devsynth.application.cli
from devsynth.application.cli.registry import COMMAND_REGISTRY

# Trigger command registration by accessing a command that will call __getattr__
_ = devsynth.application.cli.run_tests_cmd
# config_app will be imported just before use
from devsynth.core.config_loader import load_config
from devsynth.interface.cli import DEVSYNTH_THEME, CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge, sanitize_output
from devsynth.logging_setup import DevSynthLogger
from devsynth.metrics import register_dashboard_hook

if os.environ.get("DEVSYNTH_CLI_MINIMAL") == "1":  # pragma: no cover - env shim
    requirements_app = typer.Typer(
        help="Requirements commands disabled in minimal mode"
    )
    vcs_app = typer.Typer(help="VCS commands disabled in minimal mode")
    mvu_app = typer.Typer(help="MVUU commands disabled in minimal mode")
else:
    from devsynth.application.cli.mvu_commands import mvu_app
    from devsynth.application.cli.requirements_commands import requirements_app
    from devsynth.application.cli.vcs_commands import vcs_app


def init_cmd(wizard: bool = False, *, bridge: UXBridge | None = None) -> None:
    COMMAND_REGISTRY["init"](wizard=wizard, bridge=bridge)


def spec_cmd(
    requirements_file: str = "requirements.md", *, bridge: UXBridge | None = None
) -> None:
    from devsynth.application.cli import cli_commands
    from devsynth.application.cli.commands import spec_cmd as _spec_module

    _spec_module.generate_specs = cli_commands.generate_specs
    COMMAND_REGISTRY["spec"](requirements_file=requirements_file, bridge=bridge)


def test_cmd(spec_file: str = "specs.md", *, bridge: UXBridge | None = None) -> None:
    COMMAND_REGISTRY["test"](spec_file=spec_file, bridge=bridge)


def code_cmd(*, bridge: UXBridge | None = None) -> None:
    COMMAND_REGISTRY["code"](bridge=bridge)


def run_pipeline_cmd(
    *,
    target: str | None = None,
    report: str | None = None,
    bridge: UXBridge | None = None,
) -> None:
    COMMAND_REGISTRY["run-pipeline"](target=target, report=report, bridge=bridge)


def inspect_config_cmd(
    path: str | None = None, update: bool = False, prune: bool = False
) -> None:
    COMMAND_REGISTRY["inspect-config"](path=path, update=update, prune=prune)


def _patch_typer_types() -> None:
    """Allow Typer to handle custom parameter annotations used in the CLI."""

    orig = typer.main.get_click_type

    def patched_get_click_type(
        annotation: Any, parameter_info: typer.models.ParameterInfo
    ) -> click.types.ParamType:
        if annotation in {UXBridge, typer.models.Context, Any}:
            return click.STRING
        origin = getattr(annotation, "__origin__", None)
        if origin in {UXBridge, typer.models.Context, Any}:
            return click.STRING
        try:
            return orig(annotation=annotation, parameter_info=parameter_info)
        except RuntimeError:
            return click.STRING

    typer.main.get_click_type = patched_get_click_type

    orig_get_click_param = typer.main.get_click_param

    def _is_optional_union(annotation: Any) -> Tuple[bool, Tuple[Any, ...]]:
        try:
            origin = typer.main.get_origin(annotation)
        except Exception:  # pragma: no cover - defensive
            return False, ()
        if origin is None:
            return False, ()
        if not typer.main.is_union(origin):
            return False, ()
        try:
            args = tuple(typer.main.get_args(annotation))
        except Exception:  # pragma: no cover - defensive
            return False, ()
        non_none = tuple(arg for arg in args if arg is not typer.main.NoneType)
        return True, non_none

    def patched_get_click_param(
        param: typer.models.ParamMeta,
    ) -> tuple[click.Parameter, Any]:
        original_annotation = getattr(param, "annotation", typer.main.ParamMeta.empty)
        should_restore = False
        if original_annotation is not typer.main.ParamMeta.empty:
            is_union, non_none_args = _is_optional_union(original_annotation)
            if is_union and len(non_none_args) > 1:
                logger.info(
                    "Typer union fallback for parameter '%s' with annotation %r",
                    getattr(param, "name", "<unknown>"),
                    original_annotation,
                )
                param.annotation = non_none_args[0]
                should_restore = True
        try:
            logger.debug(
                "Building click parameter '%s' with annotation %r and default %r",
                getattr(param, "name", "<unknown>"),
                getattr(param, "annotation", None),
                getattr(param, "default", None),
            )
            return orig_get_click_param(param)
        except Exception as exc:  # pragma: no cover - diagnostic aid
            logger.error(
                "Failed to build click parameter '%s' with annotation %r: %s",
                getattr(param, "name", "<unknown>"),
                getattr(param, "annotation", None),
                exc,
            )
            raise
        finally:
            if should_restore:
                param.annotation = original_annotation

    typer.main.get_click_param = patched_get_click_param


logger = DevSynthLogger(__name__)


class EnhancedHelpFormatter(click.HelpFormatter):
    """Custom help formatter that provides enhanced Rich-based output."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.console = Console(theme=DEVSYNTH_THEME)

    def write_usage(self, prog: str, args: str = "", prefix: str = "Usage: ") -> None:
        """Write the usage line with enhanced formatting."""
        usage_text = f"{prefix}{prog} {args}"

        # Use Rich to format the usage text
        panel = Panel(usage_text, title="Command Usage", border_style="cyan")
        self.console.print(panel)

    def write_heading(self, heading: str) -> None:
        """Write a heading with enhanced formatting."""
        # Use Rich to format the heading
        self.console.print(f"\n[bold blue]{heading}[/bold blue]")

    def write_paragraph(self) -> None:
        """Write a paragraph separator."""
        self.console.print("")

    def write_text(self, text: str) -> None:
        """Write text with enhanced formatting."""
        # Use Rich to format the text
        if text.startswith("  "):
            # Indented text (usually option descriptions)
            self.console.print(text)
        else:
            # Regular text
            self.console.print(text)

    def write_dl(
        self,
        rows: Iterable[tuple[str, str]],
        col_max: int = 30,
        col_spacing: int = 2,
    ) -> None:
        """Write a definition list with enhanced formatting."""
        # Create a Rich table for the definition list
        table = Table(box=ROUNDED, show_header=False, expand=True)
        table.add_column("Option", style="cyan", width=col_max)
        table.add_column("Description", style="white")

        for option, description in rows:
            table.add_row(option, description)

        self.console.print(table)


class CommandHelp:
    """Container for enhanced command help information."""

    def __init__(
        self,
        summary: str,
        description: str | None = None,
        examples: list[dict[str, str]] | None = None,
        notes: list[str] | None = None,
        options: dict[str, str] | None = None,
    ) -> None:
        """Initialize the command help.

        Args:
            summary: Short summary of the command
            description: Detailed description of the command
            examples: List of example dictionaries with 'command' and 'description' keys
            notes: List of additional notes
            options: Dictionary of option names and descriptions
        """
        self.summary = summary
        self.description = description or ""
        self.examples = examples or []
        self.notes = notes or []
        self.options = options or {}

    def format(self) -> str:
        """Format the help text.

        Returns:
            The formatted help text
        """
        parts = [self.summary]

        if self.description:
            parts.append("\n" + self.description)

        if self.examples:
            parts.append("\nExamples:")
            for example in self.examples:
                parts.append(f"  $ {example['command']}")
                if "description" in example:
                    parts.append(f"      {example['description']}")

        if self.notes:
            parts.append("\nNotes:")
            for note in self.notes:
                parts.append(f"  • {note}")

        if self.options:
            parts.append("\nOptions:")
            for option, description in self.options.items():
                parts.append(f"  {option}: {description}")

        return "\n".join(parts)


def build_app() -> typer.Typer:
    """Create a Typer application with all commands registered."""
    _patch_typer_types()
    main_help = CommandHelp(
        summary="DevSynth CLI - automate iterative 'Expand, Differentiate, Refine, Retrace' workflows.",
        description=(
            "DevSynth is a tool for automating software development workflows using "
            "the EDRR (Expand, Differentiate, Refine, Retrace) methodology. It helps "
            "you generate specifications from requirements, tests from specifications, "
            "and code from tests, all while maintaining traceability and alignment."
        ),
        examples=[
            {
                "command": "devsynth init",
                "description": "Initialize a new project in the current directory",
            },
            {
                "command": "devsynth spec --requirements-file requirements.md",
                "description": "Generate specifications from requirements",
            },
            {
                "command": "devsynth test --spec-file specs.md",
                "description": "Generate tests from specifications",
            },
            {"command": "devsynth code", "description": "Generate code from tests"},
            {
                "command": "devsynth run-pipeline --target unit-tests",
                "description": "Execute the generated code",
            },
        ],
        notes=[
            "Only the embedded ChromaDB backend is currently supported.",
            "Use 'devsynth <command> --help' for more information on a specific command.",
            "Configuration can be managed with 'devsynth config' commands.",
            "Shell completion is available via '--install-completion' or the 'completion' command.",
            "Long-running commands display progress indicators for better feedback.",
            "Dashboard metric hooks can be registered with '--dashboard-hook module:function'.",
        ],
    )

    app = typer.Typer(
        help=main_help.format(),
        context_settings={"help_option_names": ["--help", "-h"]},
    )

    for name, cmd in COMMAND_REGISTRY.items():
        if name in {"config", "enable-feature"}:
            continue
        override = globals().get(f"{name.replace('-', '_')}_cmd", cmd)
        app.command(name)(override)

    app.add_typer(requirements_app, name="requirements")
    app.add_typer(mvu_app, name="mvu")
    app.add_typer(vcs_app, name="vcs", help="Git / VCS utilities")

    # Import config_app just before use to ensure lazy loading
    from devsynth.application.cli import config_app

    app.add_typer(config_app, name="config", help="Manage configuration settings")

    @app.command(
        "completion",
        help="Show or install shell completion scripts (see scripts/completions).",
    )
    def completion(
        shell: str | None = typer.Option(None, "--shell", help="Shell type"),
        install: bool = typer.Option(
            False, "--install", help="Install completion script"
        ),
        path: Path | None = typer.Option(None, "--path", help="Installation path"),
    ) -> None:
        completion_cmd(
            shell=shell, install=install, path=path
        )  # nosec B604: shell arg selects completion target

    @app.callback(invoke_without_command=True)
    def main(
        ctx: typer.Context,
        dashboard_hook: str | None = typer.Option(
            None,
            "--dashboard-hook",
            help="Python path to function receiving dashboard metric events",
        ),
        version: bool = typer.Option(  # global eager flag
            False,
            "--version",
            help="Show DevSynth version and exit",
            is_eager=True,
            callback=None,
        ),
        debug: bool = typer.Option(
            False,
            "--debug",
            help="Enable debug logging (equivalent to --log-level DEBUG)",
            is_eager=True,
        ),
        log_level: str | None = typer.Option(
            None,
            "--log-level",
            help="Set log level: DEBUG, INFO, WARNING, ERROR, CRITICAL",
            is_eager=True,
        ),
    ) -> None:
        # Handle --version eagerly
        # Configure logging as early as possible using flags/env
        import logging as _logging
        import os

        from devsynth.logging_setup import configure_logging

        # If DEVSYNTH_DEBUG is set and log_level not provided, treat as debug
        env_debug = os.environ.get("DEVSYNTH_DEBUG", "").lower() in {"1", "true", "yes"}
        chosen_level = None
        if log_level:
            chosen_level = log_level.strip().upper()
        elif debug or env_debug:
            chosen_level = "DEBUG"
        else:
            # fall back to env DEVSYNTH_LOG_LEVEL or default inside configure_logging
            chosen_level = os.environ.get("DEVSYNTH_LOG_LEVEL")

        if chosen_level:
            # Persist to env for child processes and consistency
            os.environ["DEVSYNTH_LOG_LEVEL"] = chosen_level
            try:
                configure_logging(
                    log_level=getattr(_logging, chosen_level, _logging.INFO)
                )
            except Exception:
                # Do not crash CLI due to logging issues
                pass

        # Handle --version eagerly after logging configured
        if version:
            try:
                from devsynth import __version__
            except Exception:  # pragma: no cover - defensive fallback
                __version__ = "unknown"
            typer.echo(__version__)
            raise typer.Exit(0)

        if dashboard_hook:
            try:
                module_name, func_name = dashboard_hook.split(":", 1)
                hook = getattr(importlib.import_module(module_name), func_name)
                register_dashboard_hook(hook)
            except Exception:
                typer.echo(
                    f"Failed to load dashboard hook '{dashboard_hook}'", err=True
                )
        if ctx.invoked_subcommand is None:
            typer.echo(ctx.get_help())
            raise typer.Exit()

    # Enable Typer's built-in completion if available
    if hasattr(app, "add_completion"):
        app.add_completion()
    else:  # pragma: no cover - compatibility for older Typer versions
        method = getattr(app, "_add_completion", None)
        if callable(method):
            try:
                method()
            except Exception:
                pass
    return app


# Provide a default app instance for convenience
app = build_app()


def _warn_if_features_disabled() -> None:
    """Emit a notice when all feature flags are disabled."""
    try:
        cfg = load_config()
        features = cfg.features or {}
        if features and not any(features.values()):
            typer.echo(
                "All optional features are disabled. Enable with 'devsynth config enable-feature <name>'."
            )
    except Exception:
        # Don't fail the CLI if the config can't be read
        logger.debug("Failed to read feature flags for warning message")


def show_help() -> None:
    """Display the CLI help message with enhanced formatting."""
    console = Console(theme=DEVSYNTH_THEME)

    # Create a panel with the main help text
    app = build_app()

    # Extract the help text from the app
    help_text = (app.info.help if app.info else "DevSynth CLI") or "DevSynth CLI"

    # Create a panel with the help text
    main_panel = Panel(
        Markdown(help_text), title="DevSynth CLI", subtitle="v1.0", border_style="cyan"
    )
    console.print(main_panel)

    # Create a table with the available commands
    command_table = Table(
        title="Available Commands",
        box=ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    command_table.add_column("Command", style="green")
    command_table.add_column("Description", style="white")

    # Add rows for each command
    for command in app.registered_commands:
        command_table.add_row(command.name, command.help or "")

    # Add rows for each subcommand group
    groups = []
    if hasattr(app, "registered_groups"):
        groups = app.registered_groups
    elif hasattr(app, "registered_typers"):
        # Older Typer versions store tuples of (typer_instance, name)
        for typer_instance, name in app.registered_typers:
            groups.append(
                type(
                    "_GroupInfo",
                    (),
                    {
                        "name": name,
                        "typer_instance": typer_instance,
                        "help": getattr(typer_instance.info, "help", ""),
                    },
                )()
            )
    for group in groups:
        command_table.add_row(
            f"{group.name} [subcommands]",
            (getattr(group, "help", None) or group.typer_instance.info.help or ""),
        )

    console.print(command_table)

    # Add a note about getting more help
    console.print(
        "\n[bold blue]For more information on a specific command:[/bold blue]"
    )
    console.print("  [green]devsynth [COMMAND] --help[/green]")

    # Provide a simple marker line for tests to assert
    logger.info("Commands:")
    logger.info("Run 'devsynth [COMMAND] --help' for more information on a command.")


def _format_cli_error(message: str, *, kind: str) -> str:
    """Normalize CLI error messages for actionable, concise output.

    Args:
        message: Raw error text
        kind: One of {"usage", "runtime"}
    """
    prefix = "Usage error" if kind == "usage" else "Error"
    sanitized = sanitize_output(str(message))
    # Keep messages concise; add a single actionable hint.
    hint = (
        "Run 'devsynth --help' for usage."
        if kind == "usage"
        else "Re-run with --help for usage or check logs."
    )
    return f"{prefix}: {sanitized}\n{hint}"


def parse_args(args: list[str]) -> None:
    """Parse command line arguments and execute the CLI.

    Exit codes:
    - 0: Success
    - 1: Runtime or unexpected error
    - 2: Usage or argument error
    """
    _warn_if_features_disabled()
    try:
        build_app()(args)
    except (click.UsageError, click.BadParameter) as e:
        typer.echo(_format_cli_error(str(e), kind="usage"), err=True)
        raise typer.Exit(2)
    except SystemExit:
        # Let explicit exits propagate (e.g., --help)
        raise
    except Exception as e:  # pragma: no cover - generic safety net
        typer.echo(_format_cli_error(str(e), kind="runtime"), err=True)
        raise typer.Exit(1)


def run_cli() -> None:
    """Entry point for the Typer application.

    Exit codes:
    - 0: Success
    - 1: Runtime or unexpected error
    - 2: Usage or argument error
    """
    _warn_if_features_disabled()
    try:
        build_app()()
    except (click.UsageError, click.BadParameter) as e:
        typer.echo(_format_cli_error(str(e), kind="usage"), err=True)
        raise typer.Exit(2)
    except SystemExit:
        # Let explicit exits propagate (e.g., --help)
        raise
    except Exception as e:  # pragma: no cover - generic safety net
        typer.echo(_format_cli_error(str(e), kind="runtime"), err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    run_cli()
