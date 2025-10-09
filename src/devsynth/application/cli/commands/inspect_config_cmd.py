"""Command to inspect and manage the project configuration file (``devsynth.yaml``)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Sequence, cast

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import DevSynthLogger

from ..ingest_models import (
    ManifestModel,
    ProjectStructureDirectories,
    ProjectStructureReport,
    StructureDifference,
)

logger = DevSynthLogger(__name__)
bridge: UXBridge = CLIUXBridge()


def inspect_config_cmd(
    path: Optional[str] = None,
    update: bool = False,
    prune: bool = False,
    *,
    bridge: Optional[UXBridge] = None,
) -> None:
    """Inspect and manage the project configuration file.

    Example:
        ``devsynth inspect-config --update``

    This command scans the project structure and can update, refine, or prune the configuration file
    based on the actual project structure.

    Args:
        path: Path to the project directory (default: current directory)
        update: Whether to update the configuration file with new findings
        prune: Whether to remove entries from the configuration file that no longer exist in the project
    """
    console = Console()
    bridge = bridge or globals()["bridge"]

    try:
        # Show a welcome message for the inspect-config command
        console.print(
            Panel(
                "[bold blue]DevSynth Configuration Analysis[/bold blue]\n\n"
                "This command will analyze the project configuration file (devsynth.yaml) and the project structure, "
                "and can update the configuration to reflect the actual project structure.",
                title="Configuration Analysis",
                border_style="blue",
            )
        )

        # Determine the path to analyze
        if path is None:
            path = os.getcwd()

        project_path = Path(path).resolve()
        config_path = project_path / "devsynth.yaml"
        legacy_path = project_path / "manifest.yaml"

        bridge.print(f"[bold]Analyzing project at:[/bold] {project_path}")

        # Check if devsynth.yaml or manifest.yaml exists
        if config_path.exists():
            # Use devsynth.yaml
            manifest_path = config_path
        elif legacy_path.exists():
            # Use manifest.yaml for backward compatibility
            manifest_path = legacy_path
            bridge.print(
                "[yellow]Using legacy manifest.yaml file. Consider renaming to devsynth.yaml for future compatibility.[/yellow]"
            )
        else:
            bridge.print(
                "[yellow]Warning: No configuration file found. Run 'devsynth init' to create it.[/yellow]"
            )
            return

        # Load the configuration file
        with open(manifest_path, "r") as f:
            manifest_data = yaml.safe_load(f) or {}
        if not isinstance(manifest_data, dict):
            bridge.print(
                "[red]Error analyzing configuration: Manifest content must be a mapping[/red]"
            )
            return
        manifest_model = cast(ManifestModel, manifest_data)

        # Create a progress panel
        with console.status("[bold green]Analyzing project structure...[/bold green]"):
            # Analyze the project structure
            project_structure = analyze_project_structure(project_path)

            # Compare with manifest
            differences = compare_with_manifest(manifest_model, project_structure)

        # Display the analysis results
        bridge.print("\n[bold]Analysis Results:[/bold]")

        # Display project information
        bridge.print(
            f"\n[bold]Project Name:[/bold] {manifest_model.get('projectName', 'Unknown')}"
        )
        bridge.print(
            f"[bold]Manifest Version:[/bold] {manifest_model.get('version', 'Unknown')}"
        )
        bridge.print(
            f"[bold]Last Updated:[/bold] {manifest_model.get('lastUpdated', 'Unknown')}"
        )

        # Display structure information
        structure = manifest_model.get("structure", {})
        bridge.print(f"\n[bold]Project Type:[/bold] {structure.get('type', 'Unknown')}")
        bridge.print(
            f"[bold]Primary Language:[/bold] {structure.get('primaryLanguage', 'Unknown')}"
        )

        # Display directories
        directories = structure.get("directories", {})
        if directories:
            bridge.print("\n[bold]Directories:[/bold]")
            directories_table = Table(show_header=True, header_style="bold")
            directories_table.add_column("Type")
            directories_table.add_column("Paths")

            for dir_type, paths in directories.items():
                directories_table.add_row(
                    dir_type, ", ".join(paths) if paths else "None"
                )

            console.print(directories_table)

        # Display differences
        if differences:
            bridge.print("\n[bold]Differences Found:[/bold]")
            differences_table = Table(show_header=True, header_style="bold")
            differences_table.add_column("Type")
            differences_table.add_column("Path")
            differences_table.add_column("Status")

            for diff in differences:
                differences_table.add_row(diff["type"], diff["path"], diff["status"])

            console.print(differences_table)

            # Update configuration if requested
            if update:
                updated_manifest = update_manifest(manifest_model, differences)

                with open(manifest_path, "w") as f:
                    yaml.dump(
                        updated_manifest, f, default_flow_style=False, sort_keys=False
                    )

                bridge.print("\n[green]Configuration updated successfully![/green]")

            # Prune configuration if requested
            elif prune:
                pruned_manifest = prune_manifest(manifest_model, differences)

                with open(manifest_path, "w") as f:
                    yaml.dump(
                        pruned_manifest, f, default_flow_style=False, sort_keys=False
                    )

                bridge.print("\n[green]Configuration pruned successfully![/green]")

            # Show update/prune options if not requested
            else:
                bridge.print(
                    "\n[yellow]To update the configuration with new findings, run:[/yellow]"
                )
                bridge.print("  devsynth inspect-config --update")

                bridge.print(
                    "\n[yellow]To prune entries that no longer exist, run:[/yellow]"
                )
                bridge.print("  devsynth inspect-config --prune")

                bridge.print(
                    "\n[yellow]Previously known as 'analyze-manifest'.[/yellow]"
                )
        else:
            bridge.print(
                "\n[green]No differences found. Configuration is up to date![/green]"
            )

        bridge.print("\n[green]Analysis completed successfully![/green]")

    except Exception as e:
        logger.error(f"Error analyzing configuration: {str(e)}")
        bridge.print(f"[red]Error analyzing configuration: {str(e)}[/red]")


def analyze_project_structure(project_path: Path) -> ProjectStructureReport:
    """
    Analyze the project structure and return a dictionary of findings.

    Args:
        project_path: Path to the project directory

    Returns:
        Dictionary containing the project structure
    """
    structure: ProjectStructureReport = {
        "directories": cast(
            ProjectStructureDirectories,
            {"source": [], "tests": [], "docs": []},
        ),
        "files": [],
    }

    # Common source directories
    source_dirs = ["src", "lib", "app", "source"]
    test_dirs = ["tests", "test", "spec", "specs"]
    doc_dirs = ["docs", "doc", "documentation"]

    # Scan the project directory
    for item in project_path.iterdir():
        if (
            item.is_dir()
            and not item.name.startswith(".")
            and item.name != "__pycache__"
        ):
            # Check if it's a source directory
            if item.name.lower() in source_dirs:
                structure["directories"]["source"].append(item.name)
            # Check if it's a test directory
            elif item.name.lower() in test_dirs:
                structure["directories"]["tests"].append(item.name)
            # Check if it's a documentation directory
            elif item.name.lower() in doc_dirs:
                structure["directories"]["docs"].append(item.name)
        elif item.is_file() and not item.name.startswith("."):
            structure["files"].append(item.name)

    return structure


def compare_with_manifest(
    manifest: ManifestModel, project_structure: ProjectStructureReport
) -> list[StructureDifference]:
    """
    Compare the manifest with the actual project structure and return a list of differences.

    Args:
        manifest: The manifest dictionary
        project_structure: The project structure dictionary

    Returns:
        List of differences between the manifest and the project structure
    """
    differences: list[StructureDifference] = []

    # Check directories
    manifest_dirs = manifest.get("structure", {}).get("directories", {})

    # Check source directories
    manifest_source = manifest_dirs.get("source", [])
    actual_source = project_structure["directories"]["source"]

    for dir_name in actual_source:
        if dir_name not in manifest_source:
            differences.append(
                {"type": "source", "path": dir_name, "status": "missing in manifest"}
            )

    for dir_name in manifest_source:
        if dir_name not in actual_source:
            differences.append(
                {"type": "source", "path": dir_name, "status": "missing in project"}
            )

    # Check test directories
    manifest_tests = manifest_dirs.get("tests", [])
    actual_tests = project_structure["directories"]["tests"]

    for dir_name in actual_tests:
        if dir_name not in manifest_tests:
            differences.append(
                {"type": "tests", "path": dir_name, "status": "missing in manifest"}
            )

    for dir_name in manifest_tests:
        if dir_name not in actual_tests:
            differences.append(
                {"type": "tests", "path": dir_name, "status": "missing in project"}
            )

    # Check documentation directories
    manifest_docs = manifest_dirs.get("docs", [])
    actual_docs = project_structure["directories"]["docs"]

    for dir_name in actual_docs:
        if dir_name not in manifest_docs:
            differences.append(
                {"type": "docs", "path": dir_name, "status": "missing in manifest"}
            )

    for dir_name in manifest_docs:
        if dir_name not in actual_docs:
            differences.append(
                {"type": "docs", "path": dir_name, "status": "missing in project"}
            )

    return differences


def update_manifest(
    manifest: ManifestModel, differences: Sequence[StructureDifference]
) -> ManifestModel:
    """
    Update the manifest with the differences found.

    Args:
        manifest: The manifest dictionary
        differences: List of differences between the manifest and the project structure

    Returns:
        Updated manifest dictionary
    """
    import datetime

    # Create a copy of the manifest
    updated_manifest: ManifestModel = manifest.copy()

    # Update the lastUpdated field
    updated_manifest["lastUpdated"] = datetime.datetime.now().isoformat()

    # Update directories
    for diff in differences:
        if diff["status"] == "missing in manifest":
            # Add the directory to the manifest
            dir_type = diff["type"]
            dir_path = diff["path"]

            structure = updated_manifest.setdefault("structure", {})
            directories = structure.setdefault("directories", {})
            directories.setdefault(dir_type, [])
            directories[dir_type].append(dir_path)

    return updated_manifest


def prune_manifest(
    manifest: ManifestModel, differences: Sequence[StructureDifference]
) -> ManifestModel:
    """
    Prune entries from the manifest that no longer exist in the project.

    Args:
        manifest: The manifest dictionary
        differences: List of differences between the manifest and the project structure

    Returns:
        Pruned manifest dictionary
    """
    import datetime

    # Create a copy of the manifest
    pruned_manifest: ManifestModel = manifest.copy()

    # Update the lastUpdated field
    pruned_manifest["lastUpdated"] = datetime.datetime.now().isoformat()

    # Prune directories
    for diff in differences:
        if diff["status"] == "missing in project":
            # Remove the directory from the manifest
            dir_type = diff["type"]
            dir_path = diff["path"]

            if (
                "structure" in pruned_manifest
                and "directories" in pruned_manifest["structure"]
                and dir_type in pruned_manifest["structure"]["directories"]
            ):
                if dir_path in pruned_manifest["structure"]["directories"][dir_type]:
                    pruned_manifest["structure"]["directories"][dir_type].remove(
                        dir_path
                    )

    return pruned_manifest
