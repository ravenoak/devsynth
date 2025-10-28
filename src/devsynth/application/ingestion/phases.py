from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from devsynth.exceptions import IngestionError

from . import (
    ArtifactStatus,
    ArtifactType,
    Ingestion,
    IngestionPhase,
    ProjectStructureType,
    logger,
)


def run_expand_phase(ingestion: Ingestion, dry_run: bool, verbose: bool) -> None:
    """Run the Expand phase of EDRR."""
    ingestion.metrics.start_phase(IngestionPhase.EXPAND)
    if verbose:
        logger.info("Starting Expand phase: Bottom-up discovery of all artifacts")
    try:
        from devsynth.domain.models.project import ProjectModel

        if ingestion.manifest_data is None:
            ingestion.manifest_data = {}
            logger.warning("Manifest data is not loaded. Using empty dictionary.")
        project_model = ProjectModel(ingestion.project_root, ingestion.manifest_data)
        project_model.build_model()

        model_dict = project_model.to_dict()
        ingestion.artifacts = model_dict["artifacts"]

        for relationship in model_dict["relationships"]:
            source = relationship["source"]
            target = relationship["target"]
            metadata = relationship.get("metadata", {})
            ingestion.project_graph.add_node(source)
            ingestion.project_graph.add_node(target)
            ingestion.project_graph.add_edge(source, target, **metadata)

        ingestion.metrics.artifacts_discovered = len(ingestion.artifacts)

        for artifact_data in ingestion.artifacts.values():
            artifact_type_str = artifact_data.get("type", "UNKNOWN")
            try:
                artifact_type = ArtifactType[artifact_type_str]
                ingestion.metrics.artifacts_by_type[artifact_type] += 1
            except (KeyError, ValueError):
                ingestion.metrics.artifacts_by_type[ArtifactType.UNKNOWN] += 1

        for artifact_path in ingestion.artifacts:
            ingestion.artifacts[artifact_path]["status"] = ArtifactStatus.NEW.name
            ingestion.metrics.artifacts_by_status[ArtifactStatus.NEW] += 1

        if verbose:
            logger.info(
                f"Discovered {ingestion.metrics.artifacts_discovered} artifacts during Expand phase"
            )
            for artifact_type, count in ingestion.metrics.artifacts_by_type.items():
                if count > 0:
                    logger.info(f"  - {artifact_type.name}: {count}")
    except Exception as e:
        logger.error(f"Error during Expand phase: {e}")
        ingestion.metrics.errors_encountered += 1
        raise IngestionError(f"Failed to complete Expand phase: {e}")


def run_differentiate_phase(
    ingestion: Ingestion, dry_run: bool, verbose: bool
) -> None:
    """Run the Differentiate phase of EDRR."""
    ingestion.metrics.start_phase(IngestionPhase.DIFFERENTIATE)
    if verbose:
        logger.info(
            "Starting Differentiate phase: Validation against manifest and expected structures"
        )
    try:
        if ingestion.manifest_data is None:
            ingestion.manifest_data = {}
            logger.warning("Manifest data is not loaded. Using empty dictionary.")
        structure = ingestion.manifest_data.get("structure", {})
        directories = structure.get("directories", {})

        source_dirs = directories.get("source", [])
        for src_dir in source_dirs:
            src_path = ingestion.project_root / src_dir
            if not src_path.exists():
                logger.warning(
                    f"Source directory specified in manifest does not exist: {src_path}"
                )
                ingestion.metrics.warnings_generated += 1

        project_structure = ingestion.project_structure
        if project_structure == ProjectStructureType.STANDARD:
            ingestion._validate_standard_structure(verbose)
        elif project_structure == ProjectStructureType.MONOREPO:
            ingestion._validate_monorepo_structure(verbose)
        elif project_structure == ProjectStructureType.FEDERATED:
            ingestion._validate_federated_structure(verbose)
        elif project_structure == ProjectStructureType.CUSTOM:
            ingestion._validate_custom_structure(verbose)

        ingestion._check_code_test_consistency(verbose)

        if ingestion.previous_state:
            ingestion._update_artifact_statuses(verbose)

        if verbose:
            logger.info(
                f"Completed Differentiate phase with {ingestion.metrics.warnings_generated} warnings"
            )
    except Exception as e:
        logger.error(f"Error during Differentiate phase: {e}")
        ingestion.metrics.errors_encountered += 1
        raise IngestionError(f"Failed to complete Differentiate phase: {e}")


def run_refine_phase(ingestion: Ingestion, dry_run: bool, verbose: bool) -> None:
    """Run the Refine phase of EDRR."""
    ingestion.metrics.start_phase(IngestionPhase.REFINE)
    if verbose:
        logger.info(
            "Starting Refine phase: Integration of findings into the project model"
        )
    try:
        ingestion._resolve_conflicts(verbose)
        ingestion._enrich_artifact_metadata(verbose)
        ingestion._identify_relationships(verbose)

        refined_data = {
            "project_root": str(ingestion.project_root),
            "manifest_path": str(ingestion.manifest_path),
            "project_structure": (
                ingestion.project_structure.name
                if ingestion.project_structure
                else None
            ),
            "artifacts": ingestion.artifacts,
            "metrics": ingestion.metrics.get_summary(),
            "timestamp": datetime.now().isoformat(),
        }

        if not dry_run:
            ingestion._save_refined_data(refined_data, verbose)

        if verbose:
            logger.info("Completed Refine phase successfully")
    except Exception as e:
        logger.error(f"Error during Refine phase: {e}")
        ingestion.metrics.errors_encountered += 1
        raise IngestionError(f"Failed to complete Refine phase: {e}")


def run_retrospect_phase(ingestion: Ingestion, dry_run: bool, verbose: bool) -> None:
    """Run the Retrospect phase of EDRR."""
    ingestion.metrics.start_phase(IngestionPhase.RETROSPECT)
    if verbose:
        logger.info(
            "Starting Retrospect phase: Evaluation and planning for next iteration"
        )
    try:
        evaluation = ingestion._evaluate_ingestion_process(verbose)
        improvements = ingestion._identify_improvement_areas(verbose)
        recommendations = ingestion._generate_recommendations(verbose)
        retrospective = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(ingestion.project_root),
            "manifest_path": str(ingestion.manifest_path),
            "metrics": ingestion.metrics.get_summary(),
            "evaluation": evaluation,
            "improvements": improvements,
            "recommendations": recommendations,
        }
        if not dry_run:
            ingestion._save_retrospective(retrospective, verbose)
        if verbose:
            logger.info("Completed Retrospect phase successfully")
    except Exception as e:
        logger.error(f"Error during Retrospect phase: {e}")
        ingestion.metrics.errors_encountered += 1
        raise IngestionError(f"Failed to complete Retrospect phase: {e}")
