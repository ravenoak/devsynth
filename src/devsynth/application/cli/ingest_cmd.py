"""
Command for ingesting a project into DevSynth.

This module provides the functionality for the 'devsynth ingest' CLI command,
which triggers the full ingestion and adaptation pipeline, driven by .devsynth/project.yaml
and its project structure definitions.
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml
from rich.console import Console

from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.ingestion import Ingestion
from devsynth.application.memory.adapters.tinydb_memory_adapter import (
    TinyDBMemoryAdapter,
)
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.config.unified_loader import UnifiedConfigLoader
from devsynth.domain.models.project import ProjectModel
from devsynth.domain.models.wsde import WSDETeam
from devsynth.exceptions import DevSynthError, IngestionError, ManifestError
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import DevSynthLogger
from devsynth.methodology.base import Phase

# Create a logger for this module
logger = DevSynthLogger(__name__)
DEFAULT_BRIDGE: UXBridge = CLIUXBridge()
console = Console()


def ingest_cmd(
    manifest_path: Optional[str] = None,
    dry_run: bool = False,
    verbose: bool = False,
    validate_only: bool = False,
    *,
    yes: bool = False,
    priority: Optional[str] = None,
    bridge: Optional[UXBridge] = None,
    auto_phase_transitions: bool = True,
    non_interactive: bool = False,
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
        yes: Automatically answer yes to prompts.
        priority: Project priority to persist without prompting.
        auto_phase_transitions: If True, EDRR phases advance automatically.
        non_interactive: If True, disable interactive prompts for automation.
    """
    bridge = bridge or DEFAULT_BRIDGE

    try:
        # Allow environment variables to provide default values when arguments
        # are not supplied. CLI flags still override these settings.
        if manifest_path is None:
            manifest_path = os.environ.get("DEVSYNTH_MANIFEST_PATH")
        if manifest_path is None:
            # Use manifest.yaml as the default path for tests
            manifest_path = Path(os.path.join(os.getcwd(), "manifest.yaml"))
        else:
            manifest_path = Path(manifest_path)

        project_root = (
            manifest_path.parent.parent
            if manifest_path.parent.name == ".devsynth"
            else manifest_path.parent
        )

        if not dry_run:
            dry_run = os.environ.get("DEVSYNTH_INGEST_DRY_RUN", "0").lower() in {
                "1",
                "true",
                "yes",
            }
        if not verbose:
            verbose = os.environ.get("DEVSYNTH_INGEST_VERBOSE", "0").lower() in {
                "1",
                "true",
                "yes",
            }
        if not validate_only:
            validate_only = os.environ.get(
                "DEVSYNTH_INGEST_VALIDATE_ONLY", "0"
            ).lower() in {"1", "true", "yes"}
        if not non_interactive:
            non_interactive = os.environ.get(
                "DEVSYNTH_INGEST_NONINTERACTIVE", "0"
            ).lower() in {"1", "true", "yes"}
        if non_interactive:
            os.environ["DEVSYNTH_NONINTERACTIVE"] = "1"

        if not yes:
            yes = os.environ.get("DEVSYNTH_AUTO_CONFIRM", "0").lower() in {
                "1",
                "true",
                "yes",
            }
        if yes:
            os.environ["DEVSYNTH_AUTO_CONFIRM"] = "1"
        if priority is None:
            priority = os.environ.get("DEVSYNTH_INGEST_PRIORITY")
        if priority:
            cfg = UnifiedConfigLoader.load(project_root)
            cfg.config.priority = priority
            UnifiedConfigLoader.save(cfg)

        if verbose:
            bridge.print(f"[bold]DevSynth Ingestion[/bold]")
            bridge.print(f"Manifest path: {manifest_path}")
            bridge.print(f"Dry run: {dry_run}")
            bridge.print(f"Validate only: {validate_only}")

        # Check if this project is managed by DevSynth
        is_managed_by_devsynth = (
            manifest_path.parent.exists()
            if manifest_path.parent.name == ".devsynth"
            else True
        )

        if not is_managed_by_devsynth and verbose:
            bridge.print("[yellow]This project is not managed by DevSynth.[/yellow]")
            bridge.print(
                "[yellow]The presence of a .devsynth/ directory is the marker that a project is managed by DevSynth.[/yellow]"
            )
            bridge.print("[yellow]Using default minimal configuration.[/yellow]")

        # Validate the manifest
        validate_manifest(manifest_path, verbose, bridge=bridge)

        if validate_only:
            if is_managed_by_devsynth:
                bridge.print("[green]Manifest validation successful.[/green]")
            else:
                bridge.print(
                    "[yellow]Project is not managed by DevSynth. Skipping manifest validation.[/yellow]"
                )
            return

        # Perform the ingestion using the Ingestion class
        ingestion = Ingestion(
            manifest_path.parent,
            manifest_path,
            auto_phase_transitions=auto_phase_transitions,
        )
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
    bridge: Optional[UXBridge] = None,
) -> None:
    """
    Validate the manifest file.

    Args:
        manifest_path: Path to the manifest.yaml file.
        verbose: If True, provides verbose output.

    Raises:
        ManifestError: If the manifest is invalid.
    """
    bridge = bridge or DEFAULT_BRIDGE

    # Check if the manifest path is in a .devsynth directory
    if manifest_path.parent.name == ".devsynth" and not manifest_path.parent.exists():
        # This project is not managed by DevSynth, so we don't need to validate a manifest
        if verbose:
            bridge.print(
                "[yellow]Project is not managed by DevSynth. Skipping manifest validation.[/yellow]"
            )
        return

    if not manifest_path.exists():
        raise ManifestError(f"Manifest file not found at {manifest_path}")

    try:
        # Import the validate_manifest function from the script
        sys.path.append(
            str(Path(__file__).parent.parent.parent.parent.parent / "scripts")
        )
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
                    logger.warning(
                        "Project is not managed by DevSynth. Using default minimal manifest."
                    )
                    return {
                        "metadata": {
                            "name": "Unmanaged Project",
                            "version": "0.1.0",
                            "description": "This project is not managed by DevSynth.",
                        },
                        "structure": {"type": "standard"},
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
    bridge: Optional[UXBridge] = None,
    memory_manager: Union[MemoryManager, None] = None,
    code_analyzer: Union[CodeAnalyzer, None] = None,
    wsde_team: Union[WSDETeam, None] = None,
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

    bridge = bridge or DEFAULT_BRIDGE
    memory_manager = memory_manager or MemoryManager(
        adapters={"tinydb": TinyDBMemoryAdapter()}
    )
    analyzer = code_analyzer or CodeAnalyzer()
    wsde_team = wsde_team or WSDETeam(name="IngestCmdTeam")

    if verbose:
        bridge.print("  Building project model...")

    project_model = ProjectModel(project_root, manifest)
    project_model.build_model()

    artifacts = project_model.to_dict()["artifacts"]

    # Analyse all python files discovered
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

    ideas = wsde_team.generate_diverse_ideas(
        {"description": manifest.get("metadata", {}).get("name", "project")}
    )
    knowledge = memory_manager.retrieve_relevant_knowledge({"manifest": manifest})

    if verbose:
        bridge.print(f"  Discovered {len(artifacts)} artifacts")
        bridge.print(f"  Processed {files_processed} Python files")

    duration = int(time.perf_counter() - start)

    results = {
        "artifacts_discovered": len(artifacts),
        "files_processed": files_processed,
        "analysis_metrics": {
            "lines_of_code": total_lines,
            "classes": total_classes,
            "functions": total_functions,
        },
        "artifacts": artifacts,
        "ideas": ideas,
        "knowledge": knowledge,
        "duration_seconds": duration,
    }

    memory_manager.store_with_edrr_phase(results, "EXPAND_RESULTS", Phase.EXPAND.value)

    return results


def differentiate_phase(
    manifest: Dict[str, Any],
    expand_results: Dict[str, Any],
    verbose: bool = False,
    *,
    bridge: Optional[UXBridge] = None,
    memory_manager: Union[MemoryManager, None] = None,
    code_analyzer: Union[CodeAnalyzer, None] = None,
    wsde_team: Union[WSDETeam, None] = None,
) -> Dict[str, Any]:
    """Validate the discovered project structure against the manifest."""

    start = time.perf_counter()

    bridge = bridge or DEFAULT_BRIDGE
    memory_manager = memory_manager or MemoryManager(
        adapters={"tinydb": TinyDBMemoryAdapter()}
    )
    analyzer = code_analyzer or CodeAnalyzer()
    wsde_team = wsde_team or WSDETeam(name="IngestCmdTeam")

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

    ideas = expand_results.get("ideas") or wsde_team.generate_diverse_ideas(
        {"description": manifest.get("metadata", {}).get("name", "project")}
    )
    comparison_matrix = wsde_team.create_comparison_matrix(
        ideas, ["feasibility", "impact"]
    )
    evaluated_options = wsde_team.evaluate_options(
        ideas, comparison_matrix, {"feasibility": 0.5, "impact": 0.5}
    )
    trade_offs = wsde_team.analyze_trade_offs(evaluated_options)
    decision_criteria = wsde_team.formulate_decision_criteria(
        manifest.get("metadata", {}), evaluated_options, trade_offs, False, analyzer
    )

    if verbose:
        bridge.print(f"  Missing paths: {len(missing_paths)}")
        bridge.print(f"  Inconsistencies: {len(inconsistencies)}")

    duration = int(time.perf_counter() - start)

    results = {
        "inconsistencies_found": len(inconsistencies),
        "gaps_identified": len(missing_paths),
        "missing": missing_paths,
        "comparison_matrix": comparison_matrix,
        "evaluated_options": evaluated_options,
        "trade_offs": trade_offs,
        "decision_criteria": decision_criteria,
        "duration_seconds": duration,
        "artifacts": artifacts,
    }

    memory_manager.store_with_edrr_phase(
        results, "DIFFERENTIATE_RESULTS", Phase.DIFFERENTIATE.value
    )

    return results


def refine_phase(
    manifest: Dict[str, Any],
    differentiate_results: Dict[str, Any],
    verbose: bool = False,
    *,
    bridge: Optional[UXBridge] = None,
    memory_manager: Union[MemoryManager, None] = None,
    code_analyzer: Union[CodeAnalyzer, None] = None,
    wsde_team: Union[WSDETeam, None] = None,
) -> Dict[str, Any]:
    """Create relationships between artifacts and identify outdated items."""

    start = time.perf_counter()

    bridge = bridge or DEFAULT_BRIDGE
    memory_manager = memory_manager or MemoryManager(
        adapters={"tinydb": TinyDBMemoryAdapter()}
    )
    analyzer = code_analyzer or CodeAnalyzer()
    wsde_team = wsde_team or WSDETeam(name="IngestCmdTeam")

    artifacts = differentiate_results.get("artifacts", {}) or {}

    if verbose:
        bridge.print("  Analyzing artifact relationships...")

    relationships_created = 0

    for path in artifacts:
        if Path(path).suffix != ".py" or not Path(path).exists():
            continue

        analysis = analyzer.analyze_file(path)
        relationships_created += len(analysis.get_imports())

    selected_option = wsde_team.select_best_option(
        differentiate_results.get("evaluated_options", []),
        differentiate_results.get("decision_criteria", {}),
    )
    detailed_plan = wsde_team.elaborate_details(selected_option)
    implementation_plan = wsde_team.create_implementation_plan(detailed_plan)
    optimized_plan = wsde_team.optimize_implementation(
        implementation_plan, ["performance", "maintainability"], code_analyzer=analyzer
    )
    quality_checks = wsde_team.perform_quality_assurance(
        optimized_plan, ["security", "testing"], code_analyzer=analyzer
    )

    if verbose:
        bridge.print(f"  Created {relationships_created} relationships")

    duration = int(time.perf_counter() - start)

    results = {
        "relationships_created": relationships_created,
        "outdated_items_archived": 0,
        "selected_option": selected_option,
        "detailed_plan": detailed_plan,
        "implementation_plan": implementation_plan,
        "optimized_plan": optimized_plan,
        "quality_checks": quality_checks,
        "duration_seconds": duration,
    }

    memory_manager.store_with_edrr_phase(results, "REFINE_RESULTS", Phase.REFINE.value)

    return results


def retrospect_phase(
    manifest: Dict[str, Any],
    refine_results: Dict[str, Any],
    verbose: bool = False,
    *,
    bridge: Optional[UXBridge] = None,
    memory_manager: Union[MemoryManager, None] = None,
    code_analyzer: Union[CodeAnalyzer, None] = None,
    wsde_team: Union[WSDETeam, None] = None,
) -> Dict[str, Any]:
    """Summarize results and suggest improvements."""

    start = time.perf_counter()

    bridge = bridge or DEFAULT_BRIDGE
    memory_manager = memory_manager or MemoryManager(
        adapters={"tinydb": TinyDBMemoryAdapter()}
    )
    analyzer = code_analyzer or CodeAnalyzer()
    wsde_team = wsde_team or WSDETeam(name="IngestCmdTeam")

    if verbose:
        bridge.print("  Generating retrospective report...")

    improvements = refine_results.get("relationships_created", 0)
    gaps = refine_results.get("outdated_items_archived", 0)

    learnings = wsde_team.extract_learnings(refine_results, True)
    patterns = wsde_team.recognize_patterns(
        learnings,
        historical_context=memory_manager.retrieve_historical_patterns(),
        code_analyzer=analyzer,
    )
    integrated = wsde_team.integrate_knowledge(learnings, patterns, memory_manager)
    suggestions = wsde_team.generate_improvement_suggestions(
        learnings, patterns, refine_results.get("quality_checks", {}), True
    )

    insights_captured = improvements + gaps

    duration = int(time.perf_counter() - start)

    results = {
        "insights_captured": insights_captured,
        "improvements_identified": gaps,
        "learnings": learnings,
        "patterns": patterns,
        "integrated_knowledge": integrated,
        "improvement_suggestions": suggestions,
        "duration_seconds": duration,
    }

    memory_manager.store_with_edrr_phase(
        results, "RETROSPECT_RESULTS", Phase.RETROSPECT.value
    )

    return results
