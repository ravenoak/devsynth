import typer
from devsynth.logging_setup import DevSynthLogger
from devsynth.core.config_loader import load_config

from devsynth.application.cli import (
    init_cmd,
    spec_cmd,
    test_cmd,
    code_cmd,
    run_pipeline_cmd,
    config_cmd,
    enable_feature_cmd,
    gather_cmd,
    config_app,
    inspect_cmd,
    webapp_cmd,
    webui_cmd,
    dbschema_cmd,
    doctor_cmd,
    refactor_cmd,
    analyze_code_cmd,
    edrr_cycle_cmd,
    serve_cmd,
)
from devsynth.application.cli.ingest_cmd import ingest_cmd
from devsynth.application.cli.apispec import apispec_cmd
from devsynth.application.cli.commands.align_cmd import align_cmd
from devsynth.application.cli.commands.alignment_metrics_cmd import (
    alignment_metrics_cmd,
)
from devsynth.application.cli.commands.inspect_config_cmd import inspect_config_cmd
from devsynth.application.cli.commands.validate_manifest_cmd import (
    validate_manifest_cmd,
)
from devsynth.application.cli.commands.validate_metadata_cmd import (
    validate_metadata_cmd,
)
from devsynth.application.cli.commands.test_metrics_cmd import test_metrics_cmd
from devsynth.application.cli.commands.generate_docs_cmd import generate_docs_cmd
from devsynth.application.cli.requirements_commands import requirements_app

logger = DevSynthLogger(__name__)


def build_app() -> typer.Typer:
    """Create a Typer application with all commands registered."""
    app = typer.Typer(
        help=(
            "DevSynth CLI - automate iterative 'Expand, Differentiate, Refine, "
            "Retrace' workflows. Only the embedded ChromaDB backend is currently"
            " supported."
        ),
    )

    # Mount the requirements sub-app
    app.add_typer(requirements_app, name="requirements")

    # Register commands from the application layer
    app.command(
        name="init",
        help="Initialize or onboard a project. Example: devsynth init --path ./my-project",
    )(init_cmd)
    app.command(
        name="spec",
        help="Generate specifications from requirements. Example: devsynth spec --requirements-file reqs.md",
    )(spec_cmd)
    app.command(
        name="test",
        help="Generate tests from specs. Example: devsynth test --spec-file specs.md",
    )(test_cmd)
    app.command(name="code", help="Generate code from tests. Example: devsynth code")(
        code_cmd
    )
    app.command(
        name="run-pipeline",
        help="Execute the generated code. Example: devsynth run-pipeline --target unit-tests",
    )(run_pipeline_cmd)
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
        name="dbschema",
        help="Generate a database schema. Example: devsynth dbschema --db-type sqlite",
    )(dbschema_cmd)
    app.command(
        name="doctor",
        help="Validate configuration files. Example: devsynth doctor",
    )(doctor_cmd)
    app.command(
        name="check",
        help="Alias for doctor. Example: devsynth check",
    )(doctor_cmd)
    app.command(
        name="refactor",
        help="Suggest next workflow steps. Example: devsynth refactor",
    )(refactor_cmd)
    app.command(
        name="analyze-code",
        help=(
            "Analyze a codebase and report architecture, quality and health "
            "metrics. Example: devsynth analyze-code --path ./src"
        ),
    )(analyze_code_cmd)
    app.command(
        name="edrr-cycle",
        help="Run an EDRR cycle. Example: devsynth edrr-cycle manifest.yaml",
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
        name="ingest",
        help="Ingest a project. Example: devsynth ingest manifest.yaml",
    )(ingest_cmd)
    app.command(
        name="apispec",
        help="Generate an API spec. Example: devsynth apispec",
    )(apispec_cmd)
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
    """Display the CLI help message."""
    try:
        build_app()(["--help"])
    except SystemExit:
        pass
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
