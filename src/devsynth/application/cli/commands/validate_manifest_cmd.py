"""
Command to validate the project configuration file against its schema and project structure.

This command validates the project configuration file (.devsynth/project.yaml or legacy manifest.yaml)
against its JSON schema, checks that referenced paths exist, validates dates and version formats,
and ensures the project structure is correctly represented.
"""

import json
import os
from pathlib import Path
from typing import Optional

import jsonschema
import yaml
from rich.console import Console
from rich.panel import Panel

from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
bridge: UXBridge = CLIUXBridge()


def validate_manifest_cmd(
    manifest_path: str | None = None,
    schema_path: str | None = None,
    *,
    bridge: UXBridge | None = None,
) -> None:
    """Validate the project configuration file against its schema.

    Example:
        `devsynth validate-manifest --manifest-path manifest.yaml`

    Args:
        manifest_path: Path to the project configuration file (default: .devsynth/project.yaml or manifest.yaml)
        schema_path: Path to the project schema JSON file (default: src/devsynth/schemas/project_schema.json)
    """
    console = Console()
    bridge = bridge or globals()["bridge"]

    try:
        # Show a welcome message for the validate-manifest command
        bridge.print(
            Panel(
                "[bold blue]DevSynth Project Configuration Validation[/bold blue]\n\n"
                "This command validates the project configuration file (.devsynth/project.yaml or manifest.yaml) "
                "against its JSON schema, checks that referenced paths exist, validates dates and version formats, "
                "and ensures the project structure is correctly represented.",
                title="Project Configuration Validation",
                border_style="blue",
            )
        )

        # Determine the paths
        project_root = Path(os.getcwd()).resolve()

        if manifest_path is None:
            # Check for both legacy and new manifest locations
            new_path = project_root / ".devsynth" / "project.yaml"
            legacy_path = project_root / "manifest.yaml"

            if new_path.exists():
                manifest_path = str(new_path)
            else:
                manifest_path = str(legacy_path)

        if schema_path is None:
            # Use the new schema location
            schema_path = str(
                project_root / "src" / "devsynth" / "schemas" / "project_schema.json"
            )

            # Fall back to legacy location if new location doesn't exist
            if not Path(schema_path).exists():
                legacy_schema_path = str(project_root / "docs" / "manifest_schema.json")
                if Path(legacy_schema_path).exists():
                    schema_path = legacy_schema_path

        manifest_path_obj = Path(manifest_path).resolve()
        schema_path_obj = Path(schema_path).resolve()

        bridge.print(
            f"[bold]Validating project configuration:[/bold] {manifest_path_obj}"
        )
        bridge.print(f"[bold]Using schema:[/bold] {schema_path_obj}")

        # Check if files exist
        if not manifest_path_obj.exists():
            bridge.print(
                f"[red]Error: Project configuration file not found at {manifest_path_obj}[/red]"
            )
            bridge.print(
                "[yellow]Run 'devsynth init' to create a project configuration file.[/yellow]"
            )
            return

        if not schema_path_obj.exists():
            bridge.print(
                f"[red]Error: Schema file not found at {schema_path_obj}[/red]"
            )
            return

        # Load the manifest and schema
        with open(manifest_path_obj) as f:
            manifest = yaml.safe_load(f)

        with open(schema_path_obj) as f:
            schema = json.load(f)

        # Validate against schema
        with console.status("[bold green]Validating against schema...[/bold green]"):
            try:
                jsonschema.validate(manifest, schema)
                bridge.print(
                    "[green]✓ Project configuration is valid according to schema[/green]"
                )
            except jsonschema.exceptions.ValidationError as e:
                bridge.print(f"[red]✗ Schema validation error: {e.message}[/red]")
                return

        # Validate paths exist
        with console.status("[bold green]Validating paths...[/bold green]"):
            path_errors = validate_paths_exist(manifest, project_root)
            if not path_errors:
                bridge.print("[green]✓ All referenced paths exist[/green]")
            else:
                bridge.print("[red]✗ Some referenced paths do not exist:[/red]")
                for error in path_errors:
                    bridge.print(f"  - {error}")

        # Validate dates
        with console.status("[bold green]Validating dates...[/bold green]"):
            date_errors = validate_dates(manifest)
            if not date_errors:
                bridge.print("[green]✓ All dates are valid[/green]")
            else:
                bridge.print("[red]✗ Some dates are invalid:[/red]")
                for error in date_errors:
                    bridge.print(f"  - {error}")

        # Validate version formats
        with console.status("[bold green]Validating version formats...[/bold green]"):
            version_errors = validate_version_format(manifest)
            if not version_errors:
                bridge.print("[green]✓ All version formats are valid[/green]")
            else:
                bridge.print("[red]✗ Some version formats are invalid:[/red]")
                for error in version_errors:
                    bridge.print(f"  - {error}")

        # Validate project structure
        with console.status("[bold green]Validating project structure...[/bold green]"):
            structure_errors = validate_project_structure(manifest, project_root)
            if not structure_errors:
                bridge.print("[green]✓ Project structure is valid[/green]")
            else:
                bridge.print("[red]✗ Project structure validation errors:[/red]")
                for error in structure_errors:
                    bridge.print(f"  - {error}")

        # Overall validation result
        if (
            not path_errors
            and not date_errors
            and not version_errors
            and not structure_errors
        ):
            bridge.print("\n[bold green]✓ Project configuration is valid![/bold green]")
        else:
            bridge.print(
                "\n[bold red]✗ Project configuration has validation errors.[/bold red]"
            )
            bridge.print(
                "[yellow]Run 'devsynth inspect-config --update' to update the project configuration.[/yellow]"
            )

    except Exception as err:
        bridge.print(f"[red]Error:[/red] {err}", highlight=False)


def validate_paths_exist(manifest: dict, project_root: Path) -> list:
    """
    Validate that paths referenced in the project configuration exist in the project.

    Args:
        manifest: The project configuration dictionary
        project_root: The root directory of the project

    Returns:
        A list of error messages for paths that don't exist
    """
    errors = []

    # Check key artifacts
    if "keyArtifacts" in manifest:
        for artifact_type, artifacts in manifest["keyArtifacts"].items():
            for artifact in artifacts:
                if "path" in artifact:
                    path = project_root / artifact["path"]
                    if not path.exists():
                        errors.append(
                            f"Key artifact path does not exist: {artifact['path']}"
                        )

    # Check structure directories
    if "structure" in manifest and "directories" in manifest["structure"]:
        for dir_type, dirs in manifest["structure"]["directories"].items():
            for dir_path in dirs:
                path = project_root / dir_path
                if not path.exists():
                    errors.append(f"Structure directory does not exist: {dir_path}")

    # Check entry points
    if "structure" in manifest and "entryPoints" in manifest["structure"]:
        for entry_point in manifest["structure"]["entryPoints"]:
            path = project_root / entry_point
            if not path.exists():
                errors.append(f"Entry point does not exist: {entry_point}")

    return errors


def validate_dates(manifest: dict) -> list:
    """
    Validate date formats in the project configuration.

    Args:
        manifest: The project configuration dictionary

    Returns:
        A list of error messages for invalid dates
    """
    errors = []

    # Check lastUpdated
    if "lastUpdated" in manifest:
        try:
            # Try to parse the date
            date_str = manifest["lastUpdated"]
            if isinstance(date_str, str):
                import dateutil.parser

                dateutil.parser.parse(date_str)
        except Exception:
            errors.append(f"Invalid lastUpdated date format: {manifest['lastUpdated']}")

    return errors


def validate_version_format(manifest: dict) -> list:
    """
    Validate version formats in the project configuration.

    Args:
        manifest: The project configuration dictionary

    Returns:
        A list of error messages for invalid version formats
    """
    errors = []

    # Check version
    if "version" in manifest:
        version = manifest["version"]
        if not isinstance(version, str):
            errors.append(f"Version must be a string, got {type(version).__name__}")
        elif not re.match(r"^\d+\.\d+\.\d+$", version):
            errors.append(f"Invalid version format: {version}. Expected format: X.Y.Z")

    return errors


def validate_project_structure(manifest: dict, project_root: Path) -> list:
    """
    Validate the project structure defined in the project configuration.

    Args:
        manifest: The project configuration dictionary
        project_root: The root directory of the project

    Returns:
        A list of error messages for structure validation errors
    """
    errors = []

    # Check if structure is defined
    if "structure" not in manifest:
        errors.append("No 'structure' section defined in project configuration")
        return errors

    structure = manifest["structure"]

    # Check required structure fields
    required_fields = ["type", "primaryLanguage", "directories"]
    for field in required_fields:
        if field not in structure:
            errors.append(f"Missing required field in structure: {field}")

    # Check directories
    if "directories" in structure:
        directories = structure["directories"]
        if not isinstance(directories, dict):
            errors.append("'directories' must be a dictionary")
        else:
            # Check common directory types
            common_types = ["source", "tests", "docs"]
            for dir_type in common_types:
                if dir_type not in directories:
                    errors.append(f"Missing common directory type: {dir_type}")
                elif not isinstance(directories[dir_type], list):
                    errors.append(
                        f"Directory type '{dir_type}' must be a list of paths"
                    )

    return errors


# Add missing import
import re
