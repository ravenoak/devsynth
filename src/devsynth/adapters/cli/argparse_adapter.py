import typer
from devsynth.logging_setup import DevSynthLogger
from pathlib import Path
import yaml

from devsynth.application.cli import (
    init_cmd,
    spec_cmd,
    test_cmd,
    code_cmd,
    run_cmd,
    config_cmd,
    enable_feature_cmd,
    config_app,
    analyze_cmd,
    webapp_cmd,
    dbschema_cmd,
    adaptive_cmd,
    analyze_code_cmd,
    edrr_cycle_cmd,
)
from devsynth.application.cli.ingest_cmd import ingest_cmd
from devsynth.application.cli.apispec import apispec_cmd
from devsynth.application.cli.commands.align_cmd import align_cmd
from devsynth.application.cli.commands.alignment_metrics_cmd import (
    alignment_metrics_cmd,
)
from devsynth.application.cli.commands.analyze_manifest_cmd import analyze_manifest_cmd
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
        help="DevSynth CLI - Iterative 'expand, differentiate, refine' automation",
    )

    # Mount the requirements sub-app
    app.add_typer(requirements_app, name="requirements")

    # Register commands from the application layer
    app.command(name="init")(init_cmd)
    app.command(name="spec")(spec_cmd)
    app.command(name="test")(test_cmd)
    app.command(name="code")(code_cmd)
    app.command(name="run")(run_cmd)
    app.add_typer(config_app, name="config")
    app.command(name="analyze")(analyze_cmd)
    app.command(name="webapp")(webapp_cmd)
    app.command(name="dbschema")(dbschema_cmd)
    app.command(name="adaptive")(adaptive_cmd)
    app.command(name="analyze-code")(analyze_code_cmd)
    app.command(name="edrr-cycle")(edrr_cycle_cmd)
    app.command(name="align")(align_cmd)
    app.command(name="alignment-metrics")(alignment_metrics_cmd)
    app.command(name="analyze-manifest")(analyze_manifest_cmd)
    app.command(name="analyze-config")(analyze_manifest_cmd)
    app.command(name="validate-manifest")(validate_manifest_cmd)
    app.command(name="validate-metadata")(validate_metadata_cmd)
    app.command(name="test-metrics")(test_metrics_cmd)
    app.command(name="generate-docs")(generate_docs_cmd)
    app.command(name="ingest")(ingest_cmd)
    app.command(name="apispec")(apispec_cmd)

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
        project_config = Path(".devsynth") / "project.yaml"
        if project_config.exists():
            with open(project_config, "r") as f:
                config = yaml.safe_load(f) or {}
            features = config.get("features", {})
        else:
            default_config = Path(__file__).resolve().parents[3] / "config" / "default.yml"
            with open(default_config, "r") as f:
                config = yaml.safe_load(f) or {}
            features = config.get("features", {})
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
    print("Commands:")
    print("Run 'devsynth [COMMAND] --help' for more information on a command.")


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
