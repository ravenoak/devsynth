"""Typed models used by the ingest CLI commands."""

from __future__ import annotations

from typing import Mapping, Sequence, TypeAlias, TypedDict

JSONPrimitive = str | int | float | bool | None
JSONValue: TypeAlias = JSONPrimitive | Sequence["JSONValue"] | Mapping[str, "JSONValue"]


class ManifestMetadata(TypedDict, total=False):
    """Metadata section of a manifest file."""

    name: str
    version: str
    description: str


class ManifestStructure(TypedDict, total=False):
    """Structure section describing the project layout."""

    type: str
    primaryLanguage: str
    directories: Mapping[str, Sequence[str]]


class ManifestModel(TypedDict, total=False):
    """Representation of supported manifest keys."""

    metadata: ManifestMetadata
    structure: ManifestStructure
    projectName: str
    version: str
    lastUpdated: str


class ExpandPhaseMetrics(TypedDict):
    """Metrics collected during the expand phase."""

    lines_of_code: int
    classes: int
    functions: int


class ExpandPhaseResult(TypedDict, total=False):
    """Result payload for the expand phase."""

    artifacts_discovered: int
    files_processed: int
    analysis_metrics: ExpandPhaseMetrics
    artifacts: Mapping[str, Mapping[str, JSONValue]]
    ideas: Sequence[JSONValue]
    knowledge: JSONValue | None
    duration_seconds: int


class DifferentiationPhaseResult(TypedDict, total=False):
    """Result payload for the differentiate phase."""

    inconsistencies_found: int
    gaps_identified: int
    missing: Sequence[str]
    comparison_matrix: JSONValue
    evaluated_options: JSONValue
    trade_offs: JSONValue
    decision_criteria: JSONValue
    duration_seconds: int
    artifacts: Mapping[str, Mapping[str, JSONValue]]


class RefinePhaseResult(TypedDict, total=False):
    """Result payload for the refine phase."""

    relationships_created: int
    outdated_items_archived: int
    selected_option: JSONValue
    detailed_plan: JSONValue
    implementation_plan: JSONValue
    optimized_plan: JSONValue
    quality_checks: JSONValue
    duration_seconds: int


class RetrospectPhaseResult(TypedDict, total=False):
    """Result payload for the retrospect phase."""

    insights_captured: int
    improvements_identified: int
    learnings: JSONValue
    patterns: JSONValue
    integrated_knowledge: JSONValue
    improvement_suggestions: JSONValue
    duration_seconds: int


class ProjectStructureDirectories(TypedDict):
    """Directories discovered during project inspection."""

    source: Sequence[str]
    tests: Sequence[str]
    docs: Sequence[str]


class ProjectStructureReport(TypedDict):
    """Project structure summary used by inspect-config."""

    directories: ProjectStructureDirectories
    files: Sequence[str]


class StructureDifference(TypedDict):
    """Difference entry between manifest and discovered structure."""

    type: str
    path: str
    status: str


PipelineReport = Mapping[str, JSONValue]


__all__ = [
    "JSONPrimitive",
    "JSONValue",
    "ManifestMetadata",
    "ManifestStructure",
    "ManifestModel",
    "ExpandPhaseMetrics",
    "ExpandPhaseResult",
    "DifferentiationPhaseResult",
    "RefinePhaseResult",
    "RetrospectPhaseResult",
    "ProjectStructureDirectories",
    "ProjectStructureReport",
    "StructureDifference",
    "PipelineReport",
]
