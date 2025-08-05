import inspect
from typing import Any, Dict, List, Optional

import click
import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from devsynth.application.cli import (
    code_cmd,
    config_app,
    config_cmd,
    dbschema_cmd,
    doctor_cmd,
    dpg_cmd,
    edrr_cycle_cmd,
    enable_feature_cmd,
    gather_cmd,
    init_cmd,
    inspect_cmd,
    inspect_code_cmd,
    refactor_cmd,
    run_pipeline_cmd,
    serve_cmd,
    spec_cmd,
    test_cmd,
    webapp_cmd,
    webui_cmd,
)
from devsynth.application.cli.apispec import apispec_cmd
from devsynth.application.cli.commands.align_cmd import align_cmd
from devsynth.application.cli.commands.alignment_metrics_cmd import (
    alignment_metrics_cmd,
)
from devsynth.application.cli.commands.generate_docs_cmd import generate_docs_cmd
from devsynth.application.cli.commands.inspect_config_cmd import inspect_config_cmd
from devsynth.application.cli.commands.run_tests_cmd import run_tests_cmd
from devsynth.application.cli.commands.mvuu_dashboard_cmd import mvuu_dashboard_cmd
from devsynth.application.cli.commands.mvu_init_cmd import mvu_init_cmd
from devsynth.application.cli.commands.mvu_lint_cmd import mvu_lint_cmd
from devsynth.application.cli.commands.mvu_rewrite_cmd import mvu_rewrite_cmd
from devsynth.application.cli.commands.mvu_report_cmd import mvu_report_cmd
from devsynth.application.cli.commands.security_audit_cmd import security_audit_cmd
from devsynth.application.cli.commands.test_metrics_cmd import test_metrics_cmd
from devsynth.application.cli.commands.validate_manifest_cmd import (
    validate_manifest_cmd,
)
from devsynth.application.cli.commands.validate_metadata_cmd import (
    validate_metadata_cmd,
)
from devsynth.application.cli.ingest_cmd import ingest_cmd
from devsynth.application.cli.requirements_commands import requirements_app
from devsynth.core.config_loader import load_config
from devsynth.interface.cli import DEVSYNTH_THEME
from devsynth.logging_setup import DevSynthLogger

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
    # Define enhanced help text for the main app
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
        ],
    )

    # Create the Typer app with enhanced help
    app = typer.Typer(
        help=main_help.format(),
        context_settings={"help_option_names": ["--help", "-h"]},
    )

    # Mount the requirements sub-app
    app.add_typer(requirements_app, name="requirements")

    # Register commands from the application layer with enhanced help text

    # Init command
    init_help = CommandHelp(
        summary="Initialize or onboard a project",
        description=(
            "This command sets up a new DevSynth project with the specified configuration. "
            "It creates a configuration file in the project directory and initializes "
            "the necessary directory structure. You can use the interactive wizard for "
            "a guided setup experience."
        ),
        examples=[
            {
                "command": "devsynth init",
                "description": "Initialize a project with default settings in the current directory",
            },
            {
                "command": "devsynth init --wizard",
                "description": "Start the interactive setup wizard for guided project initialization",
            },
        ],
        notes=[
            "If a project is already initialized in the current directory, the command will notify you.",
            "The wizard mode provides a step-by-step guide to configure your project.",
            "Configuration includes project language, goals, memory backend, and feature flags.",
        ],
        options={"--wizard": "Enable interactive setup wizard mode"},
    )
    app.command(
        name="init",
        help=init_help.format(),
    )(init_cmd)
    # Spec command
    spec_help = CommandHelp(
        summary="Generate specifications from requirements",
        description=(
            "This command analyzes a requirements file and generates detailed specifications. "
            "It uses natural language processing to understand the requirements and create "
            "structured specifications that can be used to generate tests. The specifications "
            "include functional requirements, non-functional requirements, and constraints."
        ),
        examples=[
            {
                "command": "devsynth spec",
                "description": "Generate specifications from the default requirements.md file",
            },
            {
                "command": "devsynth spec --requirements-file custom_requirements.md",
                "description": "Generate specifications from a custom requirements file",
            },
        ],
        notes=[
            "The requirements file should be in Markdown format.",
            "The generated specifications will be saved to specs.md by default.",
            "The command will analyze the requirements for completeness and clarity.",
            "You can review and edit the generated specifications before proceeding to the next step.",
        ],
        options={
            "--requirements-file": "Path to the requirements file (default: requirements.md)"
        },
    )
    app.command(
        name="spec",
        help=spec_help.format(),
    )(spec_cmd)

    # Test command
    test_help = CommandHelp(
        summary="Generate tests from specifications",
        description=(
            "This command analyzes a specifications file and generates comprehensive tests. "
            "It creates test cases that cover the functional requirements, edge cases, and "
            "error conditions described in the specifications. The tests are designed to "
            "validate that the implementation meets the requirements."
        ),
        examples=[
            {
                "command": "devsynth test",
                "description": "Generate tests from the default specs.md file",
            },
            {
                "command": "devsynth test --spec-file custom_specs.md",
                "description": "Generate tests from a custom specifications file",
            },
        ],
        notes=[
            "The specifications file should be in Markdown format.",
            "The generated tests will be saved to the appropriate test directories.",
            "The command will generate unit tests, integration tests, and behavior tests as appropriate.",
            "You can review and edit the generated tests before proceeding to the next step.",
        ],
        options={"--spec-file": "Path to the specifications file (default: specs.md)"},
    )
    app.command(
        name="test",
        help=test_help.format(),
    )(test_cmd)

    # Code command
    code_help = CommandHelp(
        summary="Generate code from tests",
        description=(
            "This command analyzes the test files and generates implementation code that "
            "satisfies the tests. It uses test-driven development principles to create "
            "code that meets the requirements as expressed in the tests. The generated "
            "code includes all necessary classes, methods, and functions."
        ),
        examples=[
            {
                "command": "devsynth code",
                "description": "Generate code from the existing test files",
            }
        ],
        notes=[
            "The command will analyze all test files in the project.",
            "The generated code will be saved to the appropriate source directories.",
            "The command uses the EDRR methodology to iteratively improve the code.",
            "You can review and edit the generated code before running the tests.",
        ],
    )
    app.command(name="code", help=code_help.format())(code_cmd)
    # Run-pipeline command
    run_pipeline_help = CommandHelp(
        summary="Execute the generated code and run tests",
        description=(
            "This command executes the generated code and runs the specified tests. "
            "It can run unit tests, integration tests, behavior tests, or all tests. "
            "The command provides detailed feedback on test execution, including "
            "pass/fail status, code coverage, and performance metrics."
        ),
        examples=[
            {
                "command": "devsynth run-pipeline",
                "description": "Run all tests in the project",
            },
            {
                "command": "devsynth run-pipeline --target unit-tests",
                "description": "Run only unit tests",
            },
            {
                "command": "devsynth run-pipeline --target integration-tests",
                "description": "Run only integration tests",
            },
            {
                "command": "devsynth run-pipeline --target behavior-tests",
                "description": "Run only behavior tests",
            },
        ],
        notes=[
            "The command will automatically build the project before running tests.",
            "Test results will be displayed in the console and saved to a report file.",
            "Failed tests will be highlighted with detailed error information.",
            "You can use the test results to identify issues and improve the code.",
        ],
        options={
            "--target": "Type of tests to run (unit-tests, integration-tests, behavior-tests, or all)"
        },
    )
    app.command(
        name="run-pipeline",
        help=run_pipeline_help.format(),
    )(run_pipeline_cmd)
    app.command(
        name="run-tests",
        help="Run test suites. Example: devsynth run-tests --target unit-tests",
    )(run_tests_cmd)
    app.add_typer(config_app, name="config", help="Manage configuration settings")
    app.command(
        name="inspect",
        help=(
            "Inspect a requirements file or run an interactive analysis. "
            "Example: devsynth inspect --input reqs.txt"
        ),
    )(inspect_cmd)
    app.command(
        name="gather",
        help="Interactive requirements gathering wizard",
    )(gather_cmd)
    app.command(
        name="webapp",
        help="Generate a web application. Example: devsynth webapp --framework flask",
    )(webapp_cmd)
    app.command(
        name="webui",
        help="Launch the Streamlit UI. Example: devsynth webui",
    )(webui_cmd)
    app.command(
        name="dpg",
        help="Launch the Dear PyGUI interface. Example: devsynth dpg",
    )(dpg_cmd)
    app.command(
        name="dbschema",
        help="Generate a database schema. Example: devsynth dbschema --db-type sqlite",
    )(dbschema_cmd)
    if "aliases" in inspect.signature(app.command).parameters:
        app.command(
            name="doctor",
            help="Validate configuration files. Example: devsynth doctor",
            aliases=["check"],
        )(doctor_cmd)
    else:
        app.command(
            name="doctor",
            help="Validate configuration files. Example: devsynth doctor",
        )(doctor_cmd)
    app.command(
        name="refactor",
        help="Suggest next workflow steps. Example: devsynth refactor",
    )(refactor_cmd)
    app.command(
        name="inspect-code",
        help=(
            "Inspect a codebase and report architecture, quality and health "
            "metrics. Example: devsynth inspect-code --path ./src"
        ),
    )(inspect_code_cmd)
    app.command(
        name="edrr-cycle",
        help="Run an EDRR cycle from a manifest file or prompt. Examples: devsynth edrr-cycle --manifest manifest.yaml, devsynth edrr-cycle --prompt 'Improve error handling'",
    )(edrr_cycle_cmd)
    app.command(
        name="align",
        help="Check SDLC artifact alignment. Example: devsynth align --verbose",
    )(align_cmd)
    app.command(
        name="alignment-metrics",
        help="Collect alignment metrics. Example: devsynth alignment-metrics",
    )(alignment_metrics_cmd)
    app.command(
        name="inspect-config",
        help="Inspect project configuration. Example: devsynth inspect-config",
    )(inspect_config_cmd)
    app.command(
        name="validate-manifest",
        help="Validate project config file. Example: devsynth validate-manifest",
    )(validate_manifest_cmd)
    app.command(
        name="validate-metadata",
        help="Validate documentation metadata. Example: devsynth validate-metadata --directory docs",
    )(validate_metadata_cmd)
    app.command(
        name="test-metrics",
        help="Analyze test-first metrics. Example: devsynth test-metrics --days 30",
    )(test_metrics_cmd)
    app.command(
        name="generate-docs",
        help="Generate API docs. Example: devsynth generate-docs",
    )(generate_docs_cmd)
    app.command(
        name="security-audit",
        help="Run security checks. Example: devsynth security-audit --skip-owasp",
    )(security_audit_cmd)
    app.command(
        name="ingest",
        help="Ingest a project. Example: devsynth ingest manifest.yaml",
    )(ingest_cmd)
    app.command(
        name="apispec",
        help="Generate an API spec. Example: devsynth apispec",
    )(apispec_cmd)
    app.command(
        name="mvuu-dashboard",
        help="Launch the MVUU traceability dashboard. Example: devsynth mvuu-dashboard",
    )(mvuu_dashboard_cmd)
    mvu_app = typer.Typer(help="MVU utilities")
    mvu_app.command("init", help="Scaffold MVU configuration")(mvu_init_cmd)
    mvu_app.command(
        "lint",
        help=(
            "Lint commit messages for MVUU compliance.\n\n"
            "Examples:\n  devsynth mvu lint --range origin/main..HEAD"
        ),
    )(mvu_lint_cmd)
    mvu_app.command(
        "report",
        help="Generate MVU traceability reports.",
    )(mvu_report_cmd)
    mvu_app.command(
        "rewrite",
        help="Rewrite commit history into atomic commits.",
    )(mvu_rewrite_cmd)
    app.add_typer(mvu_app, name="mvu")
    app.command(
        name="serve",
        help="Run the DevSynth API server. Example: devsynth serve --port 8080",
    )(serve_cmd)

    @app.callback(invoke_without_command=True)
    def main(ctx: typer.Context):
        if ctx.invoked_subcommand is None:
            typer.echo(ctx.get_help())
            raise typer.Exit()

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
