"""
DevSynth Ingestion Module.

This module implements the "Expand, Differentiate, Refine, Retrospect" methodology for project ingestion,
enabling DevSynth to understand and adapt to project structures as defined in manifest.yaml.
"""
import os
import logging
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple, Union
import time
from datetime import datetime
import re
import importlib.util
import networkx as nx
from enum import Enum, auto

from devsynth.exceptions import (
    IngestionError, ManifestError, DevSynthError, ConfigurationError,
    SystemError, ResourceExhaustedError
)
from devsynth.logging_setup import get_logger

# Initialize logger
logger = get_logger(__name__)


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
    NEW = auto()          # New artifact not present in previous ingestion
    CHANGED = auto()      # Modified since last ingestion
    UNCHANGED = auto()    # Existing artifact with no changes
    OUTDATED = auto()     # Artifact exists but may be outdated (references deprecated items)
    DEPRECATED = auto()   # Artifact marked for removal or replacement
    MISSING = auto()      # Artifact defined in manifest but not found


class IngestionPhase(Enum):
    """Phases of the ingestion process following EDRR methodology."""
    EXPAND = auto()       # Bottom-up discovery and integration
    DIFFERENTIATE = auto() # Top-down validation
    REFINE = auto()       # Hygiene, resilience, and integration
    RETROSPECT = auto()   # Learning and evolution


class ProjectStructureType(Enum):
    """Types of project structures that can be defined in the manifest."""
    STANDARD = auto()     # Standard single project
    MONOREPO = auto()     # Monorepo with multiple projects/packages
    FEDERATED = auto()    # Federated repositories
    COMPOSITE = auto()    # Mixed structure with submodules
    CUSTOM = auto()       # Custom structure defined by user rules


class IngestionMetrics:
    """Metrics for tracking ingestion process performance and outcomes."""

    def __init__(self):
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.artifacts_discovered = 0
        self.artifacts_by_type: Dict[ArtifactType, int] = {t: 0 for t in ArtifactType}
        self.artifacts_by_status: Dict[ArtifactStatus, int] = {s: 0 for s in ArtifactStatus}
        self.errors_encountered = 0
        self.warnings_generated = 0
        self.phase_durations: Dict[IngestionPhase, float] = {p: 0.0 for p in IngestionPhase}
        self.current_phase: Optional[IngestionPhase] = None
        self.phase_start_time: Optional[float] = None

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
        logger.info(f"Completed {self.current_phase.name} phase in {duration:.2f} seconds")
        self.current_phase = None
        self.phase_start_time = None

    def complete(self):
        """Complete the metrics collection for the entire ingestion process."""
        self.end_phase()  # End any ongoing phase
        self.end_time = time.time()

    def get_summary(self) -> Dict[str, Any]:
        """Return a summary of the ingestion metrics."""
        total_duration = (self.end_time or time.time()) - self.start_time

        return {
            "duration_seconds": total_duration,
            "artifacts": {
                "total": self.artifacts_discovered,
                "by_type": {t.name: v for t, v in self.artifacts_by_type.items()},
                "by_status": {s.name: v for s, v in self.artifacts_by_status.items()}
            },
            "phases": {p.name: duration for p, duration in self.phase_durations.items()},
            "errors": self.errors_encountered,
            "warnings": self.warnings_generated
        }


class Ingestion:
    """
    Implements the EDRR methodology for project ingestion and adaptation.

    This class manages the process of understanding and adapting to project
    structures as defined in manifest.yaml, using a four-phase approach:

    1. Expand: Bottom-up discovery of all artifacts
    2. Differentiate: Validation against manifest and expected structures
    3. Refine: Integration of findings into the project model
    4. Retrospect: Evaluation and planning for next iteration
    """

    def __init__(self, project_root: Union[str, Path], manifest_path: Optional[Union[str, Path]] = None):
        """
        Initialize the ingestion system.

        Args:
            project_root: Root directory of the project
            manifest_path: Path to manifest.yaml (defaults to project_root/manifest.yaml)
        """
        self.project_root = Path(project_root).resolve()
        self.manifest_path = Path(manifest_path) if manifest_path else self.project_root / "manifest.yaml"
        self.metrics = IngestionMetrics()
        self.project_graph = nx.DiGraph()  # Knowledge graph for project structure and relationships
        self.manifest_data: Optional[Dict[str, Any]] = None
        self.previous_state: Optional[Dict[str, Any]] = None
        self.artifacts: Dict[str, Dict[str, Any]] = {}  # Discovered artifacts
        self.project_structure: Optional[ProjectStructureType] = None

        # Ensure project root exists
        if not self.project_root.exists() or not self.project_root.is_dir():
            raise IngestionError(f"Project root does not exist or is not a directory: {self.project_root}")

        logger.info(f"Initialized ingestion for project at {self.project_root}")

    def load_manifest(self) -> Dict[str, Any]:
        """
        Load and validate the project manifest.

        Returns:
            The manifest data as a dictionary

        Raises:
            ManifestError: If the manifest is missing, invalid, or contains errors
        """
