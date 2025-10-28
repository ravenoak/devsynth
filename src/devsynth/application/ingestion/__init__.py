"""
DevSynth Ingestion Module.

This module implements the "Expand, Differentiate, Refine, Retrospect" methodology for project ingestion,
enabling DevSynth to understand and adapt to project structures as defined in .devsynth/project.yaml.
"""

import json
import os
import time
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import networkx as nx
import yaml

from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.coordinator import EDRRCoordinator
from devsynth.application.memory.adapters.tinydb_memory_adapter import (
    TinyDBMemoryAdapter,
)
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.domain.models.memory import MemoryType
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.exceptions import IngestionError, ManifestError
from devsynth.logging_setup import get_logger
from devsynth.methodology.base import Phase

# Initialize logger
logger = get_logger(__name__)

# Helper implementations for ingestion phases


class ArtifactType(Enum):
    """Types of artifacts that can be discovered during ingestion."""

    CODE = auto()
    TEST = auto()
    DOCUMENTATION = auto()
    CONFIGURATION = auto()
    BUILD = auto()
    MANIFEST = auto()
    UNKNOWN = auto()


class ArtifactStatus(Enum):
    """Status of artifacts relative to previous ingestion."""

    NEW = auto()  # New artifact not present in previous ingestion
    CHANGED = auto()  # Modified since last ingestion
    UNCHANGED = auto()  # Existing artifact with no changes
    OUTDATED = (
        auto()
    )  # Artifact exists but may be outdated (references deprecated items)
    DEPRECATED = auto()  # Artifact marked for removal or replacement
    MISSING = auto()  # Artifact defined in manifest but not found


class IngestionPhase(Enum):
    """Phases of the ingestion process following EDRR methodology."""

    EXPAND = auto()  # Bottom-up discovery and integration
    DIFFERENTIATE = auto()  # Top-down validation
    REFINE = auto()  # Hygiene, resilience, and integration
    RETROSPECT = auto()  # Learning and evolution


class ProjectStructureType(Enum):
    """Types of project structures that can be defined in the manifest."""

    STANDARD = auto()  # Standard single project
    MONOREPO = auto()  # Monorepo with multiple projects/packages
    FEDERATED = auto()  # Federated repositories
    COMPOSITE = auto()  # Mixed structure with submodules
    CUSTOM = auto()  # Custom structure defined by user rules


class IngestionMetrics:
    """Metrics for tracking ingestion process performance and outcomes."""

    def __init__(self):
        self.start_time = time.time()
        self.end_time: float | None = None
        self.artifacts_discovered = 0
        self.artifacts_by_type: dict[ArtifactType, int] = {t: 0 for t in ArtifactType}
        self.artifacts_by_status: dict[ArtifactStatus, int] = {
            s: 0 for s in ArtifactStatus
        }
        self.errors_encountered = 0
        self.warnings_generated = 0
        self.phase_durations: dict[IngestionPhase, float] = {
            p: 0.0 for p in IngestionPhase
        }
        self.current_phase: IngestionPhase | None = None
        self.phase_start_time: float | None = None

    def start_phase(self, phase: IngestionPhase):
        """Start timing for a specific phase."""
        if self.current_phase:
            self.end_phase()
        self.current_phase = phase
        self.phase_start_time = time.time()
        logger.info(f"Starting ingestion phase: {phase.name}")

    def end_phase(self):
        """End timing for the current phase and record duration."""
        if not self.current_phase or not self.phase_start_time:
            return

        duration = time.time() - self.phase_start_time
        self.phase_durations[self.current_phase] = duration
        logger.info(
            f"Completed {self.current_phase.name} phase in {duration:.2f} seconds"
        )
        self.current_phase = None
        self.phase_start_time = None

    def complete(self):
        """Complete the metrics collection for the entire ingestion process."""
        self.end_phase()  # End any ongoing phase
        self.end_time = time.time()

    def get_summary(self) -> dict[str, Any]:
        """Return a summary of the ingestion metrics."""
        total_duration = (self.end_time or time.time()) - self.start_time

        return {
            "duration_seconds": total_duration,
            "artifacts": {
                "total": self.artifacts_discovered,
                "by_type": {t.name: v for t, v in self.artifacts_by_type.items()},
                "by_status": {s.name: v for s, v in self.artifacts_by_status.items()},
            },
            "phases": {
                p.name: duration for p, duration in self.phase_durations.items()
            },
            "errors": self.errors_encountered,
            "warnings": self.warnings_generated,
        }


class Ingestion:
    """
    Implements the EDRR methodology for project ingestion and adaptation.

    This class manages the process of understanding and adapting to project
    structures as defined in .devsynth/project.yaml, using a four-phase approach:

    1. Expand: Bottom-up discovery of all artifacts
    2. Differentiate: Validation against project configuration and expected structures
    3. Refine: Integration of findings into the project model
    4. Retrospect: Evaluation and planning for next iteration
    """

    def __init__(
        self,
        project_root: str | Path,
        manifest_path: str | Path | None = None,
        edrr_coordinator: EDRRCoordinator | None = None,
        *,
        auto_phase_transitions: bool = True,
    ):
        """
        Initialize the ingestion system.

        Args:
            project_root: Root directory of the project
            manifest_path: Path to project configuration file (defaults to .devsynth/project.yaml)
            auto_phase_transitions: Whether EDRR phases should progress automatically
        """
        self.project_root = Path(project_root).resolve()

        if manifest_path:
            self.manifest_path = Path(manifest_path)
        else:
            # Use .devsynth/project.yaml as the default path
            self.manifest_path = self.project_root / ".devsynth" / "project.yaml"
        self.metrics = IngestionMetrics()
        self.project_graph = (
            nx.DiGraph()
        )  # Knowledge graph for project structure and relationships
        self.manifest_data: dict[str, Any] | None = None
        self.previous_state: dict[str, Any] | None = None
        self.artifacts: dict[str, dict[str, Any]] = {}  # Discovered artifacts
        self.project_structure: ProjectStructureType | None = None

        # Set up EDRR coordinator for phase tracking
        if edrr_coordinator is not None:
            self.edrr_coordinator = edrr_coordinator
        else:
            memory_adapter = TinyDBMemoryAdapter()
            memory_manager = MemoryManager(adapters={"tinydb": memory_adapter})
            wsde_team = WSDETeam(name="IngestionTeam")
            code_analyzer = CodeAnalyzer()
            ast_transformer = AstTransformer()
            prompt_manager = PromptManager()
            documentation_manager = DocumentationManager(memory_manager)

            self.edrr_coordinator = EDRRCoordinator(
                memory_manager=memory_manager,
                wsde_team=wsde_team,
                code_analyzer=code_analyzer,
                ast_transformer=ast_transformer,
                prompt_manager=prompt_manager,
                documentation_manager=documentation_manager,
                config={
                    "features": {"automatic_phase_transitions": auto_phase_transitions}
                },
            )

        # Ensure project root exists
        if not self.project_root.exists() or not self.project_root.is_dir():
            raise IngestionError(
                f"Project root does not exist or is not a directory: {self.project_root}"
            )

        logger.info(f"Initialized ingestion for project at {self.project_root}")

    def load_manifest(self) -> dict[str, Any]:
        """
        Load and validate the project manifest.

        Returns:
            The manifest data as a dictionary

        Raises:
            ManifestError: If the manifest is missing, invalid, or contains errors
        """
        if not self.manifest_path.exists():
            raise ManifestError(f"Manifest file not found at {self.manifest_path}")

        try:
            manifest_content = self.manifest_path.read_text(encoding="utf-8")
            manifest_data = yaml.safe_load(manifest_content)

            if not manifest_data:
                raise ManifestError("Manifest file is empty or contains invalid YAML")

            # Basic validation of required fields
            required_fields = ["metadata", "structure"]
            for field in required_fields:
                if field not in manifest_data:
                    raise ManifestError(f"Manifest is missing required field: {field}")

            # Determine project structure type
            if "structure" in manifest_data and "type" in manifest_data["structure"]:
                structure_type = manifest_data["structure"]["type"].lower()
                if structure_type == "single_package":
                    self.project_structure = ProjectStructureType.STANDARD
                elif structure_type == "monorepo":
                    self.project_structure = ProjectStructureType.MONOREPO
                elif structure_type == "multi_project_submodules":
                    self.project_structure = ProjectStructureType.FEDERATED
                elif structure_type == "custom":
                    self.project_structure = ProjectStructureType.CUSTOM
                else:
                    self.project_structure = ProjectStructureType.STANDARD
                    logger.warning(
                        f"Unknown project structure type: {structure_type}, defaulting to STANDARD"
                    )
            else:
                self.project_structure = ProjectStructureType.STANDARD
                logger.warning(
                    "No project structure type specified in manifest, defaulting to STANDARD"
                )

            # Store the manifest data
            self.manifest_data = manifest_data
            logger.info(f"Successfully loaded manifest from {self.manifest_path}")

            return manifest_data

        except yaml.YAMLError as e:
            raise ManifestError(f"Failed to parse manifest YAML: {e}")
        except Exception as e:
            raise ManifestError(f"Error loading manifest: {e}")

    def run_ingestion(
        self, dry_run: bool = False, verbose: bool = False
    ) -> dict[str, Any]:
        """
        Run the full ingestion process using the EDRR methodology.

        Args:
            dry_run: If True, analyze but don't modify any files
            verbose: If True, provide detailed output

        Returns:
            A dictionary containing the ingestion results and metrics
        """
        logger.info(f"Starting ingestion for project at {self.project_root}")

        try:
            # Load the manifest
            self.load_manifest()

            # Start EDRR cycle from the manifest. Failures here should not abort
            # the entire ingestion process so tests can run with minimal
            # manifests.
            cycle_started = True
            try:
                self.edrr_coordinator.start_cycle_from_manifest(
                    self.manifest_path, is_file=True
                )
            except Exception as e:  # pragma: no cover - defensive
                logger.error(f"Failed to start cycle from manifest: {e}")
                self.metrics.errors_encountered += 1
                cycle_started = False

            # Run the EDRR phases with coordinator tracking
            if cycle_started:
                self.edrr_coordinator.progress_to_phase(Phase.EXPAND)
            self._run_expand_phase(dry_run, verbose)
            if cycle_started:
                self.edrr_coordinator.memory_manager.store_with_edrr_phase(
                    {"summary": self.metrics.get_summary()},
                    MemoryType.INGEST_EXPAND_RESULTS,
                    Phase.EXPAND.value,
                    {"cycle_id": self.edrr_coordinator.cycle_id},
                )

            if cycle_started:
                self.edrr_coordinator.progress_to_phase(Phase.DIFFERENTIATE)
            self._run_differentiate_phase(dry_run, verbose)
            if cycle_started:
                self.edrr_coordinator.memory_manager.store_with_edrr_phase(
                    {"summary": self.metrics.get_summary()},
                    MemoryType.INGEST_DIFFERENTIATE_RESULTS,
                    Phase.DIFFERENTIATE.value,
                    {"cycle_id": self.edrr_coordinator.cycle_id},
                )

            if cycle_started:
                self.edrr_coordinator.progress_to_phase(Phase.REFINE)
            self._run_refine_phase(dry_run, verbose)
            if cycle_started:
                self.edrr_coordinator.memory_manager.store_with_edrr_phase(
                    {"summary": self.metrics.get_summary()},
                    MemoryType.INGEST_REFINE_RESULTS,
                    Phase.REFINE.value,
                    {"cycle_id": self.edrr_coordinator.cycle_id},
                )

            if cycle_started:
                self.edrr_coordinator.progress_to_phase(Phase.RETROSPECT)
            self._run_retrospect_phase(dry_run, verbose)
            if cycle_started:
                self.edrr_coordinator.memory_manager.store_with_edrr_phase(
                    {"summary": self.metrics.get_summary()},
                    MemoryType.INGEST_RETROSPECT_RESULTS,
                    Phase.RETROSPECT.value,
                    {"cycle_id": self.edrr_coordinator.cycle_id},
                )

            # Complete metrics collection
            self.metrics.complete()

            # Return results
            return {
                "success": True,
                "metrics": self.metrics.get_summary(),
                "artifacts": {
                    "total": len(self.artifacts),
                    "by_type": {
                        t.name: sum(
                            1 for a in self.artifacts.values() if a.get("type") == t
                        )
                        for t in ArtifactType
                    },
                },
                "project_structure": (
                    self.project_structure.name if self.project_structure else None
                ),
            }

        except Exception as e:
            logger.error(f"Error during ingestion: {e}")
            self.metrics.complete()

            return {
                "success": False,
                "error": str(e),
                "metrics": self.metrics.get_summary(),
            }

    def analyze_project_structure(self, verbose: bool = False) -> dict[str, Any]:
        """Analyze the project structure using the Expand phase logic."""

        self._run_expand_phase(dry_run=True, verbose=verbose)
        self.metrics.end_phase()
        result = {"artifacts": self.artifacts, "metrics": self.metrics.get_summary()}
        self.edrr_coordinator.memory_manager.store_with_edrr_phase(
            result,
            MemoryType.INGEST_EXPAND_RESULTS,
            Phase.EXPAND.value,
            {"cycle_id": self.edrr_coordinator.cycle_id},
        )
        return result

    def validate_artifacts(self, verbose: bool = False) -> dict[str, Any]:
        """Validate discovered artifacts using the Differentiate phase logic."""

        self._run_differentiate_phase(dry_run=True, verbose=verbose)
        self.metrics.end_phase()
        result = {
            "warnings": self.metrics.warnings_generated,
            "status": {
                s.name: self.metrics.artifacts_by_status[s] for s in ArtifactStatus
            },
        }
        self.edrr_coordinator.memory_manager.store_with_edrr_phase(
            result,
            MemoryType.INGEST_DIFFERENTIATE_RESULTS,
            Phase.DIFFERENTIATE.value,
            {"cycle_id": self.edrr_coordinator.cycle_id},
        )
        return result

    def remove_outdated_items(
        self, verbose: bool = False, dry_run: bool = True
    ) -> dict[str, Any]:
        """Remove or mark outdated artifacts using the Refine phase logic."""

        self._run_refine_phase(dry_run=dry_run, verbose=verbose)
        self.metrics.end_phase()
        result = {
            "status": {
                s.name: self.metrics.artifacts_by_status[s] for s in ArtifactStatus
            },
            "artifacts": self.artifacts,
        }
        self.edrr_coordinator.memory_manager.store_with_edrr_phase(
            result,
            MemoryType.INGEST_REFINE_RESULTS,
            Phase.REFINE.value,
            {"cycle_id": self.edrr_coordinator.cycle_id},
        )
        return result

    def summarize_outcomes(
        self, verbose: bool = False, dry_run: bool = True
    ) -> dict[str, Any]:
        """Summarize ingestion outcomes using the Retrospect phase logic."""

        self.metrics.start_phase(IngestionPhase.RETROSPECT)
        evaluation = self._evaluate_ingestion_process(verbose)
        improvements = self._identify_improvement_areas(verbose)
        recommendations = self._generate_recommendations(verbose)

        retrospective = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "manifest_path": str(self.manifest_path),
            "metrics": self.metrics.get_summary(),
            "evaluation": evaluation,
            "improvements": improvements,
            "recommendations": recommendations,
        }

        if not dry_run:
            self._save_retrospective(retrospective, verbose)

        self.metrics.end_phase()
        self.edrr_coordinator.memory_manager.store_with_edrr_phase(
            retrospective,
            MemoryType.INGEST_RETROSPECT_RESULTS,
            Phase.RETROSPECT.value,
            {"cycle_id": self.edrr_coordinator.cycle_id},
        )

        return retrospective

    def _run_expand_phase(self, dry_run: bool, verbose: bool) -> None:
        """Run the Expand phase of EDRR."""
        from . import phases as ingestion_phases

        ingestion_phases.run_expand_phase(self, dry_run, verbose)

    def _run_differentiate_phase(self, dry_run: bool, verbose: bool) -> None:
        """Run the Differentiate phase of EDRR."""
        from . import phases as ingestion_phases

        ingestion_phases.run_differentiate_phase(self, dry_run, verbose)

    def _validate_standard_structure(self, verbose: bool) -> None:
        """Validate the structure of a standard single-package project."""
        # Check for basic project structure
        expected_dirs = ["src", "tests", "docs"]
        missing_dirs = []

        for dir_name in expected_dirs:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                missing_dirs.append(dir_name)

        if missing_dirs and verbose:
            logger.warning(
                f"Standard project structure missing expected directories: {', '.join(missing_dirs)}"
            )
            self.metrics.warnings_generated += 1

    def _validate_monorepo_structure(self, verbose: bool) -> None:
        """Validate the structure of a monorepo project."""
        # Check for packages defined in manifest
        if self.manifest_data is None:
            # For testing purposes, initialize with an empty dict if not loaded
            self.manifest_data = {}
            logger.warning("Manifest data is not loaded. Using empty dictionary.")
        custom_layouts = self.manifest_data.get("structure", {}).get(
            "customLayouts", {}
        )

        if not custom_layouts or custom_layouts.get("type") != "monorepo":
            if verbose:
                logger.warning(
                    "Project is defined as monorepo but no monorepo layout is specified in manifest"
                )
                self.metrics.warnings_generated += 1
            return

        packages = custom_layouts.get("packages", [])
        if not packages:
            if verbose:
                logger.warning("No packages defined in monorepo layout")
                self.metrics.warnings_generated += 1
            return

        # Check if packages exist
        packages_root = custom_layouts.get("packagesRoot", "")
        packages_root_path = (
            self.project_root / packages_root if packages_root else self.project_root
        )

        missing_packages = []
        for package in packages:
            package_path = package.get("path", "")
            if not package_path:
                continue

            full_path = packages_root_path / package_path
            if not full_path.exists():
                missing_packages.append(package_path)

        if missing_packages and verbose:
            logger.warning(
                f"Missing packages defined in manifest: {', '.join(missing_packages)}"
            )
            self.metrics.warnings_generated += 1

    def _validate_federated_structure(self, verbose: bool) -> None:
        """Validate the structure of a federated project."""
        # Check for repositories defined in manifest
        if self.manifest_data is None:
            # For testing purposes, initialize with an empty dict if not loaded
            self.manifest_data = {}
            logger.warning("Manifest data is not loaded. Using empty dictionary.")
        custom_layouts = self.manifest_data.get("structure", {}).get(
            "customLayouts", {}
        )

        if not custom_layouts or custom_layouts.get("type") != "multi_project":
            if verbose:
                logger.warning(
                    "Project is defined as federated but no multi-project layout is specified in manifest"
                )
                self.metrics.warnings_generated += 1
            return

        packages = custom_layouts.get("packages", [])
        if not packages:
            if verbose:
                logger.warning("No repositories defined in federated layout")
                self.metrics.warnings_generated += 1
            return

        # Check if repositories exist
        missing_repos = []
        for package in packages:
            package_path = package.get("path", "")
            if not package_path:
                continue

            full_path = self.project_root / package_path
            if not full_path.exists():
                missing_repos.append(package_path)

        if missing_repos and verbose:
            logger.warning(
                f"Missing repositories defined in manifest: {', '.join(missing_repos)}"
            )
            self.metrics.warnings_generated += 1

    def _validate_custom_structure(self, verbose: bool) -> None:
        """Validate the structure of a custom project."""
        # For custom projects, check entry points and include patterns
        if self.manifest_data is None:
            # For testing purposes, initialize with an empty dict if not loaded
            self.manifest_data = {}
            logger.warning("Manifest data is not loaded. Using empty dictionary.")
        structure = self.manifest_data.get("structure", {})

        # Check entry points
        entry_points = structure.get("entryPoints", [])
        missing_entry_points = []

        for entry_point in entry_points:
            entry_path = self.project_root / entry_point
            if not entry_path.exists():
                missing_entry_points.append(entry_point)

        if missing_entry_points and verbose:
            logger.warning(
                f"Missing entry points defined in manifest: {', '.join(missing_entry_points)}"
            )
            self.metrics.warnings_generated += 1

    def _check_code_test_consistency(self, verbose: bool) -> None:
        """Check for consistency between code and test artifacts."""
        # Get all code artifacts
        code_artifacts = {
            path: data
            for path, data in self.artifacts.items()
            if data.get("type") == "CODE"
        }

        # Get all test artifacts
        test_artifacts = {
            path: data
            for path, data in self.artifacts.items()
            if data.get("type") == "TEST"
        }

        # Simple heuristic: check if there are tests
        if not test_artifacts and code_artifacts and verbose:
            logger.warning("Project contains code but no tests were found")
            self.metrics.warnings_generated += 1

    def _update_artifact_statuses(self, verbose: bool) -> None:
        """Update artifact statuses based on previous state."""
        if not self.previous_state or "artifacts" not in self.previous_state:
            return

        previous_artifacts = self.previous_state.get("artifacts", {})

        # Reset status counts
        for status in ArtifactStatus:
            self.metrics.artifacts_by_status[status] = 0

        # Update statuses
        for path, artifact in self.artifacts.items():
            if path in previous_artifacts:
                # Artifact existed in previous state
                prev_artifact = previous_artifacts[path]

                # Check if artifact has changed
                if self._is_artifact_changed(artifact, prev_artifact):
                    artifact["status"] = ArtifactStatus.CHANGED.name
                    self.metrics.artifacts_by_status[ArtifactStatus.CHANGED] += 1
                else:
                    artifact["status"] = ArtifactStatus.UNCHANGED.name
                    self.metrics.artifacts_by_status[ArtifactStatus.UNCHANGED] += 1
            else:
                # New artifact
                artifact["status"] = ArtifactStatus.NEW.name
                self.metrics.artifacts_by_status[ArtifactStatus.NEW] += 1

        # Check for missing artifacts
        for path, prev_artifact in previous_artifacts.items():
            if path not in self.artifacts:
                # Artifact is missing
                self.artifacts[path] = prev_artifact
                self.artifacts[path]["status"] = ArtifactStatus.MISSING.name
                self.metrics.artifacts_by_status[ArtifactStatus.MISSING] += 1

    def _is_artifact_changed(
        self, current: dict[str, Any], previous: dict[str, Any]
    ) -> bool:
        """
        Determine if an artifact has changed since the previous state.

        This is a simple comparison that can be enhanced with more sophisticated
        change detection in the future.
        """
        # For now, just check if the metadata is different
        return current.get("metadata", {}) != previous.get("metadata", {})

    def _run_refine_phase(self, dry_run: bool, verbose: bool) -> None:
        """Run the Refine phase of EDRR."""
        from . import phases as ingestion_phases

        ingestion_phases.run_refine_phase(self, dry_run, verbose)

    def _resolve_conflicts(self, verbose: bool) -> None:
        """Resolve conflicts and inconsistencies in the artifact data."""
        # Check for artifacts with the same name but different paths
        artifact_names: dict[str, str] = {}
        conflicts = []

        for path, artifact in self.artifacts.items():
            name = artifact.get("name", "")
            if not name:
                continue

            if name in artifact_names:
                # Potential conflict
                conflicts.append((name, artifact_names[name], path))
            else:
                artifact_names[name] = path

        # Log conflicts
        if conflicts and verbose:
            for name, path1, path2 in conflicts:
                logger.warning(
                    f"Name conflict: '{name}' appears in both {path1} and {path2}"
                )
                self.metrics.warnings_generated += 1

        # Mark deprecated artifacts
        for path, artifact in self.artifacts.items():
            if artifact.get("status") == ArtifactStatus.MISSING.name:
                # Mark as deprecated if it's been missing for a while
                # This is a simple heuristic that could be enhanced
                artifact["status"] = ArtifactStatus.DEPRECATED.name
                self.metrics.artifacts_by_status[ArtifactStatus.MISSING] -= 1
                self.metrics.artifacts_by_status[ArtifactStatus.DEPRECATED] += 1

                if verbose:
                    logger.info(f"Marked artifact as deprecated: {path}")

    def _enrich_artifact_metadata(self, verbose: bool) -> None:
        """Enrich artifact metadata with additional information."""
        # Add timestamp to all artifacts
        timestamp = datetime.now().isoformat()

        for path, artifact in self.artifacts.items():
            # Add last updated timestamp
            if "metadata" not in artifact:
                artifact["metadata"] = {}

            artifact["metadata"]["last_updated"] = timestamp

            # Add file size for existing files
            file_path = Path(path)
            if file_path.exists() and file_path.is_file():
                try:
                    artifact["metadata"]["size_bytes"] = file_path.stat().st_size
                except Exception as e:
                    if verbose:
                        logger.warning(f"Could not get file size for {path}: {e}")

            # Add artifact type description
            artifact_type = artifact.get("type", "UNKNOWN")
            if artifact_type == "CODE":
                artifact["metadata"]["description"] = "Source code file"
            elif artifact_type == "TEST":
                artifact["metadata"]["description"] = "Test file"
            elif artifact_type == "DOCUMENTATION":
                artifact["metadata"]["description"] = "Documentation file"
            elif artifact_type == "CONFIGURATION":
                artifact["metadata"]["description"] = "Configuration file"
            elif artifact_type == "BUILD":
                artifact["metadata"]["description"] = "Build script or configuration"

    def _identify_relationships(self, verbose: bool) -> None:
        """Identify relationships between artifacts."""
        # This is a simplified implementation that could be enhanced with
        # more sophisticated analysis (e.g., parsing imports, analyzing dependencies)

        # For now, we'll just use the project graph from the expand phase
        # and add some basic relationships based on file paths

        # Add parent-child relationships for nested directories
        for path, artifact in self.artifacts.items():
            if not Path(path).is_dir():
                continue

            # Find all artifacts that are children of this directory
            for child_path, child_artifact in self.artifacts.items():
                if child_path == path:
                    continue

                if Path(child_path).parent == Path(path):
                    # Add edge if it doesn't exist
                    if not self.project_graph.has_edge(path, child_path):
                        self.project_graph.add_edge(
                            path, child_path, relationship="contains"
                        )

        # Add relationships between test files and code files (simple heuristic)
        test_artifacts = {
            path: data
            for path, data in self.artifacts.items()
            if data.get("type") == "TEST"
        }
        code_artifacts = {
            path: data
            for path, data in self.artifacts.items()
            if data.get("type") == "CODE"
        }

        for test_path, test_artifact in test_artifacts.items():
            test_name = Path(test_path).stem

            # Look for code files that might be tested by this test
            # Simple heuristic: test_*.py might test *.py
            if test_name.startswith("test_"):
                code_name = test_name[5:]  # Remove "test_"

                for code_path, code_artifact in code_artifacts.items():
                    code_file_name = Path(code_path).stem

                    if code_file_name == code_name:
                        # Add edge if it doesn't exist
                        if not self.project_graph.has_edge(test_path, code_path):
                            self.project_graph.add_edge(
                                test_path, code_path, relationship="tests"
                            )

                            if verbose:
                                logger.info(
                                    f"Identified test relationship: {test_path} tests {code_path}"
                                )

    def _save_refined_data(self, refined_data: dict[str, Any], verbose: bool) -> None:
        """Save the refined data to disk."""
        # Create a directory for storing the refined data
        output_dir = self.project_root / ".devsynth" / "ingestion"
        os.makedirs(output_dir, exist_ok=True)

        # Generate a filename based on timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"ingestion_{timestamp}.json"

        # Save the data
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(refined_data, f, indent=2)

            if verbose:
                logger.info(f"Saved refined data to {output_file}")

            # Also save as previous state for next ingestion
            previous_state_file = output_dir / "previous_state.json"
            with open(previous_state_file, "w", encoding="utf-8") as f:
                json.dump(refined_data, f, indent=2)

            if verbose:
                logger.info(f"Updated previous state at {previous_state_file}")

        except Exception as e:
            logger.error(f"Error saving refined data: {e}")
            self.metrics.errors_encountered += 1

    def _run_retrospect_phase(self, dry_run: bool, verbose: bool) -> None:
        """Run the Retrospect phase of EDRR."""
        from . import phases as ingestion_phases

        ingestion_phases.run_retrospect_phase(self, dry_run, verbose)

    def _evaluate_ingestion_process(self, verbose: bool) -> dict[str, Any]:
        """
        Evaluate the ingestion process based on metrics and outcomes.

        Returns:
            Dictionary containing evaluation results
        """
        evaluation = {
            "success": self.metrics.errors_encountered == 0,
            "artifacts_discovered": self.metrics.artifacts_discovered,
            "errors": self.metrics.errors_encountered,
            "warnings": self.metrics.warnings_generated,
            "phase_durations": {
                p.name: duration for p, duration in self.metrics.phase_durations.items()
            },
            "artifact_types": {
                t.name: count
                for t, count in self.metrics.artifacts_by_type.items()
                if count > 0
            },
            "artifact_statuses": {
                s.name: count
                for s, count in self.metrics.artifacts_by_status.items()
                if count > 0
            },
        }

        # Calculate total duration
        total_duration = sum(self.metrics.phase_durations.values())
        evaluation["total_duration"] = total_duration

        # Calculate phase percentages
        if total_duration > 0:
            evaluation["phase_percentages"] = {
                p.name: (duration / total_duration) * 100
                for p, duration in self.metrics.phase_durations.items()
            }

        # Evaluate overall performance
        if (
            self.metrics.errors_encountered == 0
            and self.metrics.warnings_generated == 0
        ):
            evaluation["overall_assessment"] = "Excellent"
        elif (
            self.metrics.errors_encountered == 0 and self.metrics.warnings_generated < 5
        ):
            evaluation["overall_assessment"] = "Good"
        elif self.metrics.errors_encountered == 0:
            evaluation["overall_assessment"] = "Fair"
        else:
            evaluation["overall_assessment"] = "Needs improvement"

        if verbose:
            logger.info(
                f"Ingestion process evaluation: {evaluation['overall_assessment']}"
            )
            logger.info(
                f"Discovered {evaluation['artifacts_discovered']} artifacts with {evaluation['errors']} errors and {evaluation['warnings']} warnings"
            )

        return evaluation

    def _identify_improvement_areas(self, verbose: bool) -> list[dict[str, str]]:
        """
        Identify areas for improvement based on the ingestion process.

        Returns:
            List of improvement areas with descriptions
        """
        improvements = []

        if self.manifest_data is None:
            # For testing purposes, initialize with an empty dict if not loaded
            self.manifest_data = {}
            logger.warning("Manifest data is not loaded. Using empty dictionary.")

        # Check for missing manifest fields
        if not self.manifest_data.get("projectName"):
            improvements.append(
                {
                    "area": "Project Configuration",
                    "issue": "Missing project name",
                    "recommendation": "Add 'projectName' field to .devsynth/project.yaml",
                }
            )

        if not self.manifest_data.get("version"):
            improvements.append(
                {
                    "area": "Project Configuration",
                    "issue": "Missing version",
                    "recommendation": "Add 'version' field to .devsynth/project.yaml",
                }
            )

        # Check for project structure issues
        structure = self.manifest_data.get("structure", {})
        if not structure.get("directories", {}).get("source"):
            improvements.append(
                {
                    "area": "Project Structure",
                    "issue": "No source directories specified",
                    "recommendation": "Add source directories to .devsynth/project.yaml",
                }
            )

        # Check for test coverage
        code_artifacts_count = self.metrics.artifacts_by_type.get(ArtifactType.CODE, 0)
        test_artifacts_count = self.metrics.artifacts_by_type.get(ArtifactType.TEST, 0)

        if code_artifacts_count > 0 and test_artifacts_count == 0:
            improvements.append(
                {
                    "area": "Testing",
                    "issue": "No test artifacts found",
                    "recommendation": "Add tests for your code",
                }
            )
        elif (
            code_artifacts_count > 0
            and test_artifacts_count / code_artifacts_count < 0.5
        ):
            improvements.append(
                {
                    "area": "Testing",
                    "issue": "Low test coverage",
                    "recommendation": "Increase test coverage for your code",
                }
            )

        # Check for documentation
        doc_artifacts_count = self.metrics.artifacts_by_type.get(
            ArtifactType.DOCUMENTATION, 0
        )
        if code_artifacts_count > 0 and doc_artifacts_count == 0:
            improvements.append(
                {
                    "area": "Documentation",
                    "issue": "No documentation artifacts found",
                    "recommendation": "Add documentation for your code",
                }
            )

        # Check for performance issues
        slowest_phase = max(
            self.metrics.phase_durations.items(), key=lambda x: x[1], default=(None, 0)
        )
        if (
            slowest_phase[0] and slowest_phase[1] > 5.0
        ):  # If a phase took more than 5 seconds
            improvements.append(
                {
                    "area": "Performance",
                    "issue": f"Slow {slowest_phase[0].name} phase ({slowest_phase[1]:.2f} seconds)",
                    "recommendation": f"Optimize {slowest_phase[0].name} phase processing",
                }
            )

        if verbose and improvements:
            logger.info(f"Identified {len(improvements)} areas for improvement")
            for improvement in improvements:
                logger.info(f"  - {improvement['area']}: {improvement['issue']}")

        return improvements

    def _generate_recommendations(self, verbose: bool) -> list[dict[str, str]]:
        """
        Generate recommendations for the next iteration.

        Returns:
            List of recommendations with descriptions
        """
        recommendations = []

        # Recommend based on project structure
        if self.project_structure == ProjectStructureType.STANDARD:
            # For standard projects, recommend basic structure improvements
            recommendations.append(
                {
                    "category": "Project Structure",
                    "recommendation": "Consider organizing code into modules for better maintainability",
                    "priority": "Medium",
                }
            )
        elif self.project_structure == ProjectStructureType.MONOREPO:
            # For monorepo projects, recommend package management
            recommendations.append(
                {
                    "category": "Project Structure",
                    "recommendation": "Consider using a monorepo management tool like Lerna or Nx",
                    "priority": "Medium",
                }
            )

        # Recommend based on artifact types
        if self.metrics.artifacts_by_type.get(ArtifactType.CONFIGURATION, 0) > 10:
            recommendations.append(
                {
                    "category": "Configuration",
                    "recommendation": "Consider consolidating configuration files to reduce complexity",
                    "priority": "Medium",
                }
            )

        # Recommend based on artifact statuses
        if self.metrics.artifacts_by_status.get(ArtifactStatus.DEPRECATED, 0) > 0:
            recommendations.append(
                {
                    "category": "Code Cleanup",
                    "recommendation": "Remove deprecated artifacts to reduce technical debt",
                    "priority": "High",
                }
            )

        # Always recommend updating the project configuration
        recommendations.append(
            {
                "category": "Project Configuration",
                "recommendation": "Keep .devsynth/project.yaml updated as the project evolves",
                "priority": "High",
            }
        )

        # Recommend running ingestion regularly
        recommendations.append(
            {
                "category": "Process",
                "recommendation": "Run ingestion regularly to keep project model up to date",
                "priority": "Medium",
            }
        )

        if verbose:
            logger.info(
                f"Generated {len(recommendations)} recommendations for next iteration"
            )
            for recommendation in recommendations:
                logger.info(
                    f"  - {recommendation['category']} ({recommendation['priority']}): {recommendation['recommendation']}"
                )

        return recommendations

    def _save_retrospective(self, retrospective: dict[str, Any], verbose: bool) -> None:
        """Save the retrospective report to disk."""
        # Create a directory for storing the retrospective
        output_dir = self.project_root / ".devsynth" / "ingestion" / "retrospectives"
        os.makedirs(output_dir, exist_ok=True)

        # Generate a filename based on timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"retrospective_{timestamp}.json"

        # Save the data
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(retrospective, f, indent=2)

            if verbose:
                logger.info(f"Saved retrospective report to {output_file}")

            # Also generate a markdown summary for human readability
            markdown_file = output_dir / f"retrospective_{timestamp}.md"
            self._generate_markdown_summary(retrospective, markdown_file)

            if verbose:
                logger.info(f"Generated markdown summary at {markdown_file}")

        except Exception as e:
            logger.error(f"Error saving retrospective: {e}")
            self.metrics.errors_encountered += 1

    def _generate_markdown_summary(
        self, retrospective: dict[str, Any], output_file: Path
    ) -> None:
        """Generate a markdown summary of the retrospective report."""
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                # Write header
                f.write(f"# DevSynth Ingestion Retrospective\n\n")
                f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(
                    f"**Project:** {retrospective.get('project_root', 'Unknown')}\n"
                )
                f.write(
                    f"**Overall Assessment:** {retrospective.get('evaluation', {}).get('overall_assessment', 'Unknown')}\n\n"
                )

                # Write metrics summary
                f.write(f"## Metrics Summary\n\n")
                metrics = retrospective.get("metrics", {})
                f.write(
                    f"- **Duration:** {metrics.get('duration_seconds', 0):.2f} seconds\n"
                )
                f.write(
                    f"- **Artifacts:** {metrics.get('artifacts', {}).get('total', 0)}\n"
                )
                f.write(f"- **Errors:** {metrics.get('errors', 0)}\n")
                f.write(f"- **Warnings:** {metrics.get('warnings', 0)}\n\n")

                # Write artifact types
                artifact_types = retrospective.get("evaluation", {}).get(
                    "artifact_types", {}
                )
                if artifact_types:
                    f.write(f"### Artifact Types\n\n")
                    for artifact_type, count in artifact_types.items():
                        f.write(f"- **{artifact_type}:** {count}\n")
                    f.write("\n")

                # Write improvement areas
                improvements = retrospective.get("improvements", [])
                if improvements:
                    f.write(f"## Improvement Areas\n\n")
                    for improvement in improvements:
                        f.write(f"### {improvement.get('area', 'Unknown')}\n\n")
                        f.write(f"**Issue:** {improvement.get('issue', 'Unknown')}\n\n")
                        f.write(
                            f"**Recommendation:** {improvement.get('recommendation', 'Unknown')}\n\n"
                        )

                # Write recommendations
                recommendations = retrospective.get("recommendations", [])
                if recommendations:
                    f.write(f"## Recommendations for Next Iteration\n\n")
                    for recommendation in recommendations:
                        f.write(
                            f"### {recommendation.get('category', 'Unknown')} (Priority: {recommendation.get('priority', 'Unknown')})\n\n"
                        )
                        f.write(
                            f"{recommendation.get('recommendation', 'Unknown')}\n\n"
                        )

                # Write footer
                f.write(f"---\n\n")
                f.write(
                    f"*This report was generated automatically by DevSynth Ingestion.*\n"
                )

        except Exception as e:
            logger.error(f"Error generating markdown summary: {e}")
            self.metrics.errors_encountered += 1
