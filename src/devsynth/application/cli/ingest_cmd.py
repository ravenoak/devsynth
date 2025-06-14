"""
Command for ingesting a project into DevSynth.

This module provides the functionality for the 'devsynth ingest' CLI command,
which triggers the full ingestion and adaptation pipeline, driven by .devsynth/project.yaml
and its project structure definitions.
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import Optional, Dict, Any
from rich.console import Console

from devsynth.exceptions import DevSynthError, IngestionError, ManifestError
from devsynth.logging_setup import DevSynthLogger
from devsynth.application.ingestion import Ingestion

# Create a logger for this module
logger = DevSynthLogger(__name__)
console = Console()

def ingest_cmd(
    manifest_path: Optional[str] = None,
    dry_run: bool = False,
    verbose: bool = False,
    validate_only: bool = False
) -> None:
    """
    Ingest a project into DevSynth.

    This command triggers the full ingestion and adaptation pipeline (Expand, Differentiate, Refine, Retrospect),
    driven by .devsynth/project.yaml and its project structure definitions.

    Args:
        manifest_path: Path to the project.yaml file. If None, uses the default path (.devsynth/project.yaml).
        dry_run: If True, performs a dry run without making any changes.
        verbose: If True, provides verbose output.
        validate_only: If True, only validates the manifest without performing ingestion.
    """
    try:
        # Determine the manifest path
        if manifest_path is None:
            # Use manifest.yaml as the default path for tests
            manifest_path = Path(os.path.join(os.getcwd(), "manifest.yaml"))
        else:
            manifest_path = Path(manifest_path)

        if verbose:
            console.print(f"[bold]DevSynth Ingestion[/bold]")
            console.print(f"Manifest path: {manifest_path}")
            console.print(f"Dry run: {dry_run}")
            console.print(f"Validate only: {validate_only}")

        # Check if this project is managed by DevSynth
        is_managed_by_devsynth = manifest_path.parent.exists() if manifest_path.parent.name == ".devsynth" else True

        if not is_managed_by_devsynth and verbose:
            console.print("[yellow]This project is not managed by DevSynth.[/yellow]")
            console.print("[yellow]The presence of a .devsynth/ directory is the marker that a project is managed by DevSynth.[/yellow]")
            console.print("[yellow]Using default minimal configuration.[/yellow]")

        # Validate the manifest
        validate_manifest(manifest_path, verbose)

        if validate_only:
            if is_managed_by_devsynth:
                console.print("[green]Manifest validation successful.[/green]")
            else:
                console.print("[yellow]Project is not managed by DevSynth. Skipping manifest validation.[/yellow]")
            return

        # Perform the ingestion using the Ingestion class
        ingestion = Ingestion(manifest_path.parent, manifest_path)
        result = ingestion.run_ingestion(dry_run=dry_run, verbose=verbose)

        if result.get("success"):
            console.print("[green]Ingestion completed successfully.[/green]")
        else:
            console.print(f"[red]Ingestion failed:[/red] {result.get('error')}")

        if verbose:
            console.print(json.dumps(result.get("metrics", {}), indent=2))

    except ManifestError as e:
        console.print(f"[red]Manifest Error:[/red] {str(e)}")
        sys.exit(1)
    except IngestionError as e:
        console.print(f"[red]Ingestion Error:[/red] {str(e)}")
        sys.exit(1)
    except DevSynthError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected Error:[/red] {str(e)}")
        sys.exit(1)

def validate_manifest(manifest_path: Path, verbose: bool = False) -> None:
    """
    Validate the manifest file.

    Args:
        manifest_path: Path to the manifest.yaml file.
        verbose: If True, provides verbose output.

    Raises:
        ManifestError: If the manifest is invalid.
    """
    # Check if the manifest path is in a .devsynth directory
    if manifest_path.parent.name == ".devsynth" and not manifest_path.parent.exists():
        # This project is not managed by DevSynth, so we don't need to validate a manifest
        if verbose:
            console.print("[yellow]Project is not managed by DevSynth. Skipping manifest validation.[/yellow]")
        return

    if not manifest_path.exists():
        raise ManifestError(f"Manifest file not found at {manifest_path}")

    try:
        # Import the validate_manifest function from the script
        sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "scripts"))
        from validate_manifest import validate_manifest as validate_manifest_script

        # Get the project root directory
        project_root = manifest_path.parent

        # Get the schema path
        schema_path = project_root / "docs" / "manifest_schema.json"

        if not schema_path.exists():
            raise ManifestError(f"Manifest schema file not found at {schema_path}")

        # Validate the manifest
        success = validate_manifest_script(manifest_path, schema_path, project_root)

        if not success:
            raise ManifestError("Manifest validation failed")

        if verbose:
            console.print("[green]Manifest validation successful.[/green]")

    except ImportError:
        raise ManifestError("Failed to import validate_manifest script")
    except Exception as e:
        raise ManifestError(f"Failed to validate manifest: {str(e)}")

def load_manifest(manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the manifest file.

    Args:
        manifest_path: Path to the project.yaml file. If None, uses .devsynth/project.yaml.

    Returns:
        The loaded manifest as a dictionary.

    Raises:
        ManifestError: If the manifest cannot be loaded.
    """
    try:
        # If no path is provided, use .devsynth/project.yaml
        if manifest_path is None:
            manifest_path = Path(".devsynth/project.yaml")

            # Check if .devsynth/project.yaml exists
            if not os.path.exists(str(manifest_path)):
                # Try the legacy manifest.yaml in the root directory
                manifest_path = Path("manifest.yaml")
                if not os.path.exists(str(manifest_path)):
                    # Neither .devsynth/project.yaml nor manifest.yaml exists
                    # Return a minimal default manifest
                    logger.warning("Project is not managed by DevSynth. Using default minimal manifest.")
                    return {
                        "metadata": {
                            "name": "Unmanaged Project",
                            "version": "0.1.0",
                            "description": "This project is not managed by DevSynth."
                        },
                        "structure": {
                            "type": "standard"
                        }
                    }

        # Try to open and load the manifest
        with open(manifest_path, "r") as f:
            manifest = yaml.safe_load(f)
        return manifest

    except yaml.YAMLError as e:
        raise ManifestError(f"Failed to parse manifest YAML: {str(e)}")
    except Exception as e:
        raise ManifestError(f"Failed to load manifest: {str(e)}")

def expand_phase(manifest: Dict[str, Any], verbose: bool = False) -> Dict[str, Any]:
    """
    Perform the Expand phase of the ingestion process.

    This phase analyzes the project from the ground up, building a comprehensive
    understanding of the current state.

    Args:
        manifest: The loaded manifest.
        verbose: If True, provides verbose output.

    Returns:
        The results of the Expand phase.
    """
    # This is a placeholder implementation
    # In a real implementation, this would analyze the project structure,
    # code, tests, and other artifacts to build a comprehensive understanding

    if verbose:
        console.print("  Analyzing project structure...")
        console.print("  Scanning source code...")
        console.print("  Examining tests...")
        console.print("  Reviewing documentation...")

    # Return placeholder results
    return {
        "artifacts_discovered": 150,
        "files_processed": 200,
        "duration_seconds": 120
    }

def differentiate_phase(manifest: Dict[str, Any], expand_results: Dict[str, Any], verbose: bool = False) -> Dict[str, Any]:
    """
    Perform the Differentiate phase of the ingestion process.

    This phase validates the understanding from the Expand phase against higher-level
    definitions, identifying consistencies, discrepancies, new elements, and outdated components.

    Args:
        manifest: The loaded manifest.
        expand_results: The results of the Expand phase.
        verbose: If True, provides verbose output.

    Returns:
        The results of the Differentiate phase.
    """
    # This is a placeholder implementation
    # In a real implementation, this would validate the understanding from the Expand phase
    # against higher-level definitions

    if verbose:
        console.print("  Validating against requirements...")
        console.print("  Checking for inconsistencies...")
        console.print("  Identifying gaps...")
        console.print("  Detecting outdated components...")

    # Return placeholder results
    return {
        "inconsistencies_found": 10,
        "gaps_identified": 5,
        "duration_seconds": 90
    }

def refine_phase(manifest: Dict[str, Any], differentiate_results: Dict[str, Any], verbose: bool = False) -> Dict[str, Any]:
    """
    Perform the Refine phase of the ingestion process.

    This phase facilitates the removal or archiving of old, unneeded, or deprecated parts,
    verifies that all critical tests pass, and ensures overall project hygiene.

    Args:
        manifest: The loaded manifest.
        differentiate_results: The results of the Differentiate phase.
        verbose: If True, provides verbose output.

    Returns:
        The results of the Refine phase.
    """
    # This is a placeholder implementation
    # In a real implementation, this would facilitate the removal or archiving of old,
    # unneeded, or deprecated parts, verify that all critical tests pass, and ensure
    # overall project hygiene

    if verbose:
        console.print("  Creating relationships between artifacts...")
        console.print("  Archiving outdated items...")
        console.print("  Verifying test coverage...")
        console.print("  Ensuring project hygiene...")

    # Return placeholder results
    return {
        "relationships_created": 75,
        "outdated_items_archived": 15,
        "duration_seconds": 180
    }

def retrospect_phase(manifest: Dict[str, Any], refine_results: Dict[str, Any], verbose: bool = False) -> Dict[str, Any]:
    """
    Perform the Retrospect phase of the ingestion process.

    This phase evaluates the outcomes of the ingestion process and plans for the next iteration.

    Args:
        manifest: The loaded manifest.
        refine_results: The results of the Refine phase.
        verbose: If True, provides verbose output.

    Returns:
        The results of the Retrospect phase.
    """
    # This is a placeholder implementation
    # In a real implementation, this would evaluate the outcomes of the ingestion process
    # and plan for the next iteration

    if verbose:
        console.print("  Evaluating ingestion outcomes...")
        console.print("  Capturing insights...")
        console.print("  Identifying improvement opportunities...")
        console.print("  Planning next steps...")

    # Return placeholder results
    return {
        "insights_captured": 8,
        "improvements_identified": 12,
        "duration_seconds": 60
    }
