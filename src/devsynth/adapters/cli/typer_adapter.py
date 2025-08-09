from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from devsynth.application.cli import config_app
from devsynth.application.cli.registry import COMMAND_REGISTRY
from devsynth.application.cli.requirements_commands import requirements_app
from devsynth.core.config_loader import load_config
from devsynth.interface.cli import DEVSYNTH_THEME, CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import DevSynthLogger


def init_cmd(wizard: bool = False, *, bridge: Optional[UXBridge] = None) -> None:
    COMMAND_REGISTRY["init"](wizard=wizard, bridge=bridge)


def spec_cmd(
    requirements_file: str = "requirements.md", *, bridge: Optional[UXBridge] = None
) -> None:
    from devsynth.application.cli import cli_commands
    from devsynth.application.cli.commands import spec_cmd as _spec_module

    _spec_module.generate_specs = cli_commands.generate_specs
    COMMAND_REGISTRY["spec"](requirements_file=requirements_file, bridge=bridge)


def test_cmd(spec_file: str = "specs.md", *, bridge: Optional[UXBridge] = None) -> None:
    COMMAND_REGISTRY["test"](spec_file=spec_file, bridge=bridge)


def code_cmd(*, bridge: Optional[UXBridge] = None) -> None:
    COMMAND_REGISTRY["code"](bridge=bridge)


def run_pipeline_cmd(
    *,
    target: Optional[str] = None,
    report: Optional[str] = None,
    bridge: Optional[UXBridge] = None,
) -> None:
    COMMAND_REGISTRY["run-pipeline"](target=target, report=report, bridge=bridge)


def inspect_config_cmd(
    path: Optional[str] = None, update: bool = False, prune: bool = False
) -> None:
    COMMAND_REGISTRY["inspect-config"](path=path, update=update, prune=prune)


def completion_cmd(
    shell: Optional[str] = None,
    install: bool = False,
    path: Optional[Path] = None,
    *,
    bridge: Optional[UXBridge] = None,
) -> None:
    """Generate or install shell completion scripts."""

    bridge = bridge or CLIUXBridge()
    progress = bridge.create_progress("Generating completion script", total=2)
    app = build_app()
    from click.shell_completion import get_completion_class

    shell_name = shell or "bash"
    completion_cls = get_completion_class(shell_name)
    comp = completion_cls(app, {}, "devsynth", "_DEVSYNTH_COMPLETE")
    script = comp.source()
    progress.update(status="Script generated", advance=1)

    if install:
        target = path or Path.home() / f".devsynth-completion.{shell_name}"
        target.write_text(script)
        bridge.show_completion(str(target))
    else:
        bridge.show_completion(script)

    progress.complete()


def _patch_typer_types() -> None:
    """Allow Typer to handle custom parameter annotations used in the CLI."""

    orig = typer.main.get_click_type

    def patched_get_click_type(*, annotation, parameter_info):  # type: ignore[override]
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


logger = DevSynthLogger(__name__)


class EnhancedHelpFormatter(click.HelpFormatter):
    """Custom help formatter that provides more detailed and better formatted help text."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.console = Console(theme=DEVSYNTH_THEME)

    def write_usage(self, prog, args="", prefix="Usage: "):
        """Write the usage line with enhanced formatting."""
        usage_text = f"{prefix}{prog} {args}"

        # Use Rich to format the usage text
        panel = Panel(usage_text, title="Command Usage", border_style="cyan")
        self.console.print(panel)

    def write_heading(self, heading):
        """Write a heading with enhanced formatting."""
        # Use Rich to format the heading
        self.console.print(f"\n[bold blue]{heading}[/bold blue]")

    def write_paragraph(self):
        """Write a paragraph separator."""
        self.console.print("")

    def write_text(self, text):
        """Write text with enhanced formatting."""
        # Use Rich to format the text
        if text.startswith("  "):
            # Indented text (usually option descriptions)
            self.console.print(text)
        else:
            # Regular text
            self.console.print(text)

    def write_dl(self, rows, col_max=30, col_spacing=2):
        """Write a definition list with enhanced formatting."""
        # Create a Rich table for the definition list
        table = Table(box=ROUNDED, show_header=False, expand=True)
        table.add_column("Option", style="cyan", width=col_max)
        table.add_column("Description", style="white")

        for row in rows:
            option, description = row
            table.add_row(option, description)

        self.console.print(table)


class CommandHelp:
    """Container for enhanced command help information."""

    def __init__(
        self,
        summary: str,
        description: str = None,
        examples: List[Dict[str, str]] = None,
        notes: List[str] = None,
        options: Dict[str, str] = None,
    ):
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
    app.add_typer(config_app, name="config", help="Manage configuration settings")

    @app.command(
        "completion",
        help="Show or install shell completion scripts (see scripts/completions).",
    )
    def completion(
        shell: Optional[str] = typer.Option(None, "--shell", help="Shell type"),
        install: bool = typer.Option(
            False, "--install", help="Install completion script"
        ),
        path: Optional[Path] = typer.Option(None, "--path", help="Installation path"),
    ) -> None:
        completion_cmd(shell=shell, install=install, path=path)

    @app.callback(invoke_without_command=True)
    def main(ctx: typer.Context):
        if ctx.invoked_subcommand is None:
            typer.echo(ctx.get_help())
            raise typer.Exit()

    # Enable Typer's built-in completion if available
    if hasattr(app, "add_completion"):
        app.add_completion()
    else:  # pragma: no cover - compatibility for older Typer versions
        try:
            app._add_completion()  # type: ignore[attr-defined]
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
    help_text = app.info.help or "DevSynth CLI"

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


def parse_args(args: list[str]) -> None:
    """Parse command line arguments and execute the CLI."""
    _warn_if_features_disabled()
    build_app()(args)


def run_cli() -> None:
    """Entry point for the Typer application."""
    _warn_if_features_disabled()
    build_app()()


if __name__ == "__main__":
    run_cli()
