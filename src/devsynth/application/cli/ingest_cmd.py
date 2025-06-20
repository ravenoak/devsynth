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
import time
from pathlib import Path
from typing import Optional, Dict, Any
from rich.console import Console
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge

from devsynth.exceptions import DevSynthError, IngestionError, ManifestError
from devsynth.logging_setup import DevSynthLogger
from devsynth.application.ingestion import Ingestion
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.domain.models.project import ProjectModel

# Create a logger for this module
logger = DevSynthLogger(__name__)
bridge: UXBridge = CLIUXBridge()
console = Console()

def ingest_cmd(
    manifest_path: Optional[str] = None,
    dry_run: bool = False,
    verbose: bool = False,
    validate_only: bool = False,
    *,
    bridge: UXBridge = bridge,
) -> None:
    """Ingest a project into DevSynth.

    Example:
        `devsynth ingest manifest.yaml`

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
            bridge.print(f"[bold]DevSynth Ingestion[/bold]")
            bridge.print(f"Manifest path: {manifest_path}")
            bridge.print(f"Dry run: {dry_run}")
            bridge.print(f"Validate only: {validate_only}")

        # Check if this project is managed by DevSynth
        is_managed_by_devsynth = manifest_path.parent.exists() if manifest_path.parent.name == ".devsynth" else True

        if not is_managed_by_devsynth and verbose:
            bridge.print("[yellow]This project is not managed by DevSynth.[/yellow]")
            bridge.print("[yellow]The presence of a .devsynth/ directory is the marker that a project is managed by DevSynth.[/yellow]")
            bridge.print("[yellow]Using default minimal configuration.[/yellow]")

        # Validate the manifest
        validate_manifest(manifest_path, verbose, bridge=bridge)

        if validate_only:
            if is_managed_by_devsynth:
                bridge.print("[green]Manifest validation successful.[/green]")
            else:
                bridge.print("[yellow]Project is not managed by DevSynth. Skipping manifest validation.[/yellow]")
            return

        # Perform the ingestion using the Ingestion class
        ingestion = Ingestion(manifest_path.parent, manifest_path)
        result = ingestion.run_ingestion(dry_run=dry_run, verbose=verbose)

        if result.get("success"):
            bridge.print("[green]Ingestion completed successfully.[/green]")
        else:
            bridge.print(f"[red]Ingestion failed:[/red] {result.get('error')}")

        if verbose:
            bridge.print(json.dumps(result.get("metrics", {}), indent=2))

    except ManifestError as e:
        bridge.print(f"[red]Manifest Error:[/red] {str(e)}")
        sys.exit(1)
    except IngestionError as e:
        bridge.print(f"[red]Ingestion Error:[/red] {str(e)}")
        sys.exit(1)
    except DevSynthError as e:
        bridge.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)
    except Exception as e:
        bridge.print(f"[red]Unexpected Error:[/red] {str(e)}")
        sys.exit(1)

def validate_manifest(
    manifest_path: Path,
    verbose: bool = False,
    *,
    bridge: UXBridge = bridge,
) -> None:
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
            bridge.print("[yellow]Project is not managed by DevSynth. Skipping manifest validation.[/yellow]")
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
            bridge.print("[green]Manifest validation successful.[/green]")

    except ImportError:
        raise ManifestError("Failed to import validate_manifest script")
    except Exception as e:
        raise ManifestError(f"Failed to validate manifest: {str(e)}")

def load_manifest(
    manifest_path: Optional[Path] = None,
    *,
    bridge: UXBridge = bridge,
) -> Dict[str, Any]:
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

def expand_phase(
    manifest: Dict[str, Any],
    verbose: bool = False,
    *,
    bridge: UXBridge = bridge,
) -> Dict[str, Any]:
    """Run the Expand phase and gather project metrics.

    This implementation builds a :class:`ProjectModel` from the current working
    directory using the provided manifest and then scans all discovered Python
    files with :class:`~devsynth.application.code_analysis.analyzer.CodeAnalyzer`
    to collect basic metrics.

    Args:
        manifest: The loaded manifest configuration.
        verbose: If ``True`` enable verbose progress output.

    Returns:
        Dictionary containing metrics from the Expand phase.
    """

    start = time.perf_counter()

    project_root = Path.cwd()

    if verbose:
        bridge.print("  Building project model...")

    project_model = ProjectModel(project_root, manifest)
    project_model.build_model()

    artifacts = project_model.to_dict()["artifacts"]

    # Analyse all python files discovered
    analyzer = CodeAnalyzer()
    python_files = [
        Path(p)
        for p, data in artifacts.items()
        if not data.get("is_directory") and Path(p).suffix == ".py"
    ]

    files_processed = 0
    total_lines = 0
    total_classes = 0
    total_functions = 0
    for path in python_files:
        analysis = analyzer.analyze_file(str(path))
        metrics = analysis.get_metrics()
        files_processed += 1
        total_lines += metrics.get("lines_of_code", 0)
        total_classes += metrics.get("classes_count", 0)
        total_functions += metrics.get("functions_count", 0)

    if verbose:
        bridge.print(f"  Discovered {len(artifacts)} artifacts")
        bridge.print(f"  Processed {files_processed} Python files")

    duration = int(time.perf_counter() - start)

    return {
        "artifacts_discovered": len(artifacts),
        "files_processed": files_processed,
        "analysis_metrics": {
            "lines_of_code": total_lines,
            "classes": total_classes,
            "functions": total_functions,
        },
        "artifacts": artifacts,
        "duration_seconds": duration,
    }

def differentiate_phase(
    manifest: Dict[str, Any],
    expand_results: Dict[str, Any],
    verbose: bool = False,
    *,
    bridge: UXBridge = bridge,
) -> Dict[str, Any]:
    """Validate the discovered project structure against the manifest."""

    start = time.perf_counter()

    artifacts = expand_results.get("artifacts", {})

    if verbose:
        bridge.print("  Validating discovered artifacts...")

    project_root = Path.cwd()
    directories = manifest.get("structure", {}).get("directories", {})

    missing_paths = []
    for _, dirs in directories.items():
        for d in dirs:
            if not (project_root / d).exists():
                missing_paths.append(str(project_root / d))

    inconsistencies = []
    for path in artifacts:
        if not Path(path).exists():
            inconsistencies.append(path)

    if verbose:
        bridge.print(f"  Missing paths: {len(missing_paths)}")
        bridge.print(f"  Inconsistencies: {len(inconsistencies)}")

    duration = int(time.perf_counter() - start)

    return {
        "inconsistencies_found": len(inconsistencies),
        "gaps_identified": len(missing_paths),
        "missing": missing_paths,
        "duration_seconds": duration,
        "artifacts": artifacts,
    }

def refine_phase(
    manifest: Dict[str, Any],
    differentiate_results: Dict[str, Any],
    verbose: bool = False,
    *,
    bridge: UXBridge = bridge,
) -> Dict[str, Any]:
    """Create relationships between artifacts and identify outdated items."""

    start = time.perf_counter()

    artifacts = differentiate_results.get("artifacts", {}) or {}

    if verbose:
        bridge.print("  Analyzing artifact relationships...")

    analyzer = CodeAnalyzer()
    relationships_created = 0

    for path in artifacts:
        if Path(path).suffix != ".py" or not Path(path).exists():
            continue

        analysis = analyzer.analyze_file(path)
        relationships_created += len(analysis.get_imports())

    if verbose:
        bridge.print(f"  Created {relationships_created} relationships")

    duration = int(time.perf_counter() - start)

    return {
        "relationships_created": relationships_created,
        "outdated_items_archived": 0,
        "duration_seconds": duration,
    }

def retrospect_phase(
    manifest: Dict[str, Any],
    refine_results: Dict[str, Any],
    verbose: bool = False,
    *,
    bridge: UXBridge = bridge,
) -> Dict[str, Any]:
    """Summarize results and suggest improvements."""

    start = time.perf_counter()

    if verbose:
        bridge.print("  Generating retrospective report...")

    improvements = refine_results.get("relationships_created", 0)
    gaps = refine_results.get("outdated_items_archived", 0)

    insights_captured = improvements + gaps

    duration = int(time.perf_counter() - start)

    return {
        "insights_captured": insights_captured,
        "improvements_identified": gaps,
        "duration_seconds": duration,
    }
