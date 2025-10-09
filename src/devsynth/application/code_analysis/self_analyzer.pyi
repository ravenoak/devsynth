"""Type hints for devsynth.application.code_analysis.self_analyzer."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, TypedDict

from devsynth.application.code_analysis.analyzer import (
    ClassInfo,
    CodeAnalyzer,
    FunctionInfo,
    ImportInfo,
    SymbolReference,
    VariableInfo,
)
from devsynth.domain.models.code_analysis import CodeAnalysis

class ArchitectureViolation(TypedDict):
    source_layer: str
    target_layer: str
    description: str

class ArchitectureInsights(TypedDict):
    type: str
    confidence: float
    layers: Dict[str, List[str]]
    layer_dependencies: Dict[str, Set[str]]
    architecture_violations: List[ArchitectureViolation]

class DocstringCoverage(TypedDict):
    files: float
    classes: float
    functions: float

class CodeQualityInsights(TypedDict):
    docstring_coverage: DocstringCoverage
    total_files: int
    total_classes: int
    total_functions: int

class TestCoverageInsights(TypedDict):
    total_symbols: int
    tested_symbols: int
    coverage_percentage: float

class ImprovementOpportunity(TypedDict):
    type: str
    description: str
    priority: str

MetricsSummary = Dict[str, Any]

class SelfAnalysisInsights(TypedDict):
    metrics_summary: MetricsSummary
    architecture: ArchitectureInsights
    code_quality: CodeQualityInsights
    test_coverage: TestCoverageInsights
    improvement_opportunities: List[ImprovementOpportunity]

class SerializableFileAnalysis(TypedDict):
    imports: List[ImportInfo]
    classes: List[ClassInfo]
    functions: List[FunctionInfo]
    variables: List[VariableInfo]
    docstring: str
    metrics: Dict[str, Any]

class CodeAnalysisSnapshot(TypedDict):
    files: Dict[str, SerializableFileAnalysis]
    symbols: Dict[str, List[SymbolReference]]
    dependencies: Dict[str, List[str]]
    metrics: Dict[str, Any]

class SelfAnalysisResult(TypedDict):
    code_analysis: CodeAnalysisSnapshot
    insights: SelfAnalysisInsights

class SelfAnalyzer:
    code_analyzer: CodeAnalyzer
    project_root: str

    def __init__(self, project_root: Optional[str] = ...) -> None: ...
    def analyze(self, target_dir: Optional[str] = ...) -> SelfAnalysisResult: ...
    def _generate_insights(
        self, code_analysis: CodeAnalysis
    ) -> SelfAnalysisInsights: ...
