"""
Self-analysis capabilities for DevSynth.

This module provides classes and functions for DevSynth to analyze its own codebase
and generate insights that can be used for self-improvement.
"""

import ast
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, TypedDict, cast

from devsynth.application.code_analysis.analyzer import (
    ClassInfo,
    CodeAnalyzer,
    FunctionInfo,
    ImportInfo,
    SymbolReference,
    VariableInfo,
)
from devsynth.domain.models.code_analysis import CodeAnalysis, FileAnalysis
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


class ArchitectureViolation(TypedDict):
    """Violation detected between two architectural layers."""

    source_layer: str
    target_layer: str
    description: str


class ArchitectureInsights(TypedDict):
    """Structured representation of architecture analysis."""

    type: str
    confidence: float
    layers: dict[str, list[str]]
    layer_dependencies: dict[str, set[str]]
    architecture_violations: list[ArchitectureViolation]


class DocstringCoverage(TypedDict):
    """Coverage ratios for docstrings across artefacts."""

    files: float
    classes: float
    functions: float


class CodeQualityInsights(TypedDict):
    """Summary of code quality metrics extracted from the analysis."""

    docstring_coverage: DocstringCoverage
    total_files: int
    total_classes: int
    total_functions: int


class TestCoverageInsights(TypedDict):
    """Summary of inferred test coverage."""

    total_symbols: int
    tested_symbols: int
    coverage_percentage: float


class ImprovementOpportunity(TypedDict):
    """Actionable opportunity derived from the analysis."""

    type: str
    description: str
    priority: str


MetricsSummary = dict[str, Any]


class SelfAnalysisInsights(TypedDict):
    """Aggregated insights returned to callers."""

    metrics_summary: MetricsSummary
    architecture: ArchitectureInsights
    code_quality: CodeQualityInsights
    test_coverage: TestCoverageInsights
    improvement_opportunities: list[ImprovementOpportunity]


class SerializableFileAnalysis(TypedDict):
    """Serializable representation of a :class:`FileAnalysis`."""

    imports: list[ImportInfo]
    classes: list[ClassInfo]
    functions: list[FunctionInfo]
    variables: list[VariableInfo]
    docstring: str
    metrics: dict[str, Any]


class CodeAnalysisSnapshot(TypedDict):
    """Serializable representation of :class:`CodeAnalysis`."""

    files: dict[str, SerializableFileAnalysis]
    symbols: dict[str, list[SymbolReference]]
    dependencies: dict[str, list[str]]
    metrics: dict[str, Any]


class SelfAnalysisResult(TypedDict):
    """Typed return signature for :meth:`SelfAnalyzer.analyze`."""

    code_analysis: CodeAnalysisSnapshot
    insights: SelfAnalysisInsights


class SelfAnalyzer:
    """
    Analyzer for DevSynth's own codebase.

    This class provides capabilities for DevSynth to analyze its own codebase
    and generate insights that can be used for self-improvement.
    """

    def __init__(self, project_root: str | None = None):
        """
        Initialize the SelfAnalyzer.

        Args:
            project_root: The root directory of the DevSynth project.
                          If None, it will be determined automatically.
        """
        self.code_analyzer = CodeAnalyzer()

        # Determine the project root if not provided
        if project_root is None:
            # Try to find the project root by looking for the pyproject.toml file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            while current_dir != os.path.dirname(
                current_dir
            ):  # Stop at filesystem root
                if os.path.exists(os.path.join(current_dir, "pyproject.toml")):
                    project_root = current_dir
                    break
                current_dir = os.path.dirname(current_dir)

        if project_root is None:
            raise ValueError(
                "Could not determine the project root. Please provide it explicitly."
            )

        self.project_root = project_root
        logger.info(f"SelfAnalyzer initialized with project root: {self.project_root}")

    def analyze(self, target_dir: str | None = None) -> SelfAnalysisResult:
        """
        Analyze a codebase and generate insights.

        Args:
            target_dir: Directory to analyze. If None, analyzes the project root.

        Returns:
            A dictionary containing analysis results and insights.
        """
        if target_dir is None:
            # If no target directory is specified, use the project root
            target_dir = self.project_root
            logger.info(f"Starting analysis of project at {target_dir}")
        else:
            logger.info(f"Starting analysis of directory at {target_dir}")

        try:
            # Analyze the source code
            code_analysis = self.code_analyzer.analyze_directory(target_dir)

            # Generate insights
            insights = self._generate_insights(code_analysis)

            # Combine analysis and insights
            analysis_snapshot = cast(CodeAnalysisSnapshot, code_analysis.to_dict())
            result: SelfAnalysisResult = {
                "code_analysis": analysis_snapshot,
                "insights": insights,
            }

            logger.info("Self-analysis completed")
            return result
        except Exception as e:
            # Graceful fallback for error paths – do not raise, return safe shape
            logger.error(f"SelfAnalyzer.analyze failed: {e}")
            safe_insights: SelfAnalysisInsights = {
                "metrics_summary": {},
                "architecture": {
                    "type": "unknown",
                    "confidence": 0.0,
                    "layers": {},
                    "layer_dependencies": {},
                    "architecture_violations": [],
                },
                "code_quality": {
                    "docstring_coverage": {
                        "files": 0.0,
                        "classes": 0.0,
                        "functions": 0.0,
                    },
                    "total_files": 0,
                    "total_classes": 0,
                    "total_functions": 0,
                },
                "test_coverage": {
                    "total_symbols": 0,
                    "tested_symbols": 0,
                    "coverage_percentage": 0.0,
                },
                "improvement_opportunities": [],
            }
            safe_code_analysis: CodeAnalysisSnapshot = {
                "files": {},
                "symbols": {},
                "dependencies": {},
                "metrics": {},
            }
            return {"code_analysis": safe_code_analysis, "insights": safe_insights}

    def _generate_insights(self, code_analysis: CodeAnalysis) -> SelfAnalysisInsights:
        """
        Generate insights from the code analysis.

        Args:
            code_analysis: The result of analyzing the codebase.

        Returns:
            A dictionary containing insights about the codebase.
        """
        logger.info("Generating insights from code analysis")

        # Extract metrics
        metrics: MetricsSummary = code_analysis.get_metrics()

        # Analyze architecture
        architecture_insights = self._analyze_architecture(code_analysis)

        # Analyze code quality
        code_quality_insights = self._analyze_code_quality(code_analysis)

        # Analyze test coverage
        test_coverage_insights = self._analyze_test_coverage(code_analysis)

        # Identify improvement opportunities
        improvement_opportunities = self._identify_improvement_opportunities(
            code_analysis,
            architecture_insights,
            code_quality_insights,
            test_coverage_insights,
        )

        return {
            "metrics_summary": metrics,
            "architecture": architecture_insights,
            "code_quality": code_quality_insights,
            "test_coverage": test_coverage_insights,
            "improvement_opportunities": improvement_opportunities,
        }

    def _analyze_architecture(
        self, code_analysis: CodeAnalysis
    ) -> ArchitectureInsights:
        """
        Analyze the architecture of the codebase.

        Args:
            code_analysis: The result of analyzing the codebase.

        Returns:
            A dictionary containing insights about the architecture.
        """
        logger.info("Analyzing architecture")

        # Detect architecture type
        architecture_type, confidence = self._detect_architecture_type(code_analysis)

        # Identify layers based on package structure
        layers = self._identify_layers(code_analysis)

        # Identify components within each layer
        for file_path in code_analysis.get_files().keys():
            try:
                relative_path = os.path.relpath(file_path, self.project_root)
                parts = relative_path.split(os.sep)

                # Skip very short paths
                if len(parts) < 2:
                    continue

                # For typical project structures, the first level directories are often layers
                potential_layer = parts[0]

                # If we're in a src directory, look at the next level
                if potential_layer == "src" and len(parts) >= 2:
                    potential_layer = parts[1]

                    # If the next level is the project name, look one level deeper
                    project_name = os.path.basename(self.project_root)
                    if potential_layer == project_name and len(parts) >= 3:
                        potential_layer = parts[2]

                # If this is a recognized layer, add the component
                if potential_layer in layers:
                    component = (
                        parts[min(len(parts) - 1, parts.index(potential_layer) + 1)]
                        if len(parts) > parts.index(potential_layer) + 1
                        else ""
                    )
                    if component and component not in layers[potential_layer]:
                        layers[potential_layer].append(component)
            except Exception as e:
                logger.warning(f"Error processing file path {file_path}: {str(e)}")
                continue

        # Analyze layer dependencies
        layer_dependencies = self._analyze_layer_dependencies(code_analysis, layers)

        # Check for architecture violations
        architecture_violations = self._check_architecture_violations(
            layer_dependencies, architecture_type
        )

        return {
            "type": architecture_type,
            "confidence": confidence,
            "layers": layers,
            "layer_dependencies": layer_dependencies,
            "architecture_violations": architecture_violations,
        }

    def _detect_architecture_type(
        self, code_analysis: CodeAnalysis
    ) -> tuple[str, float]:
        """
        Detect the type of architecture used in the codebase.

        Args:
            code_analysis: The result of analyzing the codebase.

        Returns:
            A tuple containing the architecture type and confidence score.
        """
        logger.info("Detecting architecture type")

        # Get all file paths
        file_paths = list(code_analysis.get_files().keys())

        # Check for hexagonal architecture
        hexagonal_score = self._check_hexagonal_architecture(file_paths)

        # Check for MVC architecture
        mvc_score = self._check_mvc_architecture(file_paths)

        # Check for layered architecture
        layered_score = self._check_layered_architecture(file_paths)

        # Check for microservices architecture
        microservices_score = self._check_microservices_architecture(file_paths)

        # Determine the most likely architecture type
        architecture_scores = {
            "Hexagonal": hexagonal_score,
            "MVC": mvc_score,
            "Layered": layered_score,
            "Microservices": microservices_score,
            "Unknown": 0.1,  # Default score for unknown architecture
        }

        architecture_type = max(architecture_scores, key=architecture_scores.get)
        confidence = architecture_scores[architecture_type]

        logger.info(
            f"Detected architecture type: {architecture_type} (confidence: {confidence:.2f})"
        )

        return architecture_type, confidence

    def _check_hexagonal_architecture(self, file_paths: list[str]) -> float:
        """
        Check if the codebase follows a hexagonal architecture.

        Args:
            file_paths: List of file paths in the codebase.

        Returns:
            A confidence score between 0 and 1.
        """
        # Look for typical hexagonal architecture directories
        hexagonal_patterns = [
            r"domain",
            r"application",
            r"adapters",
            r"ports",
            r"infrastructure",
            r"interfaces",
        ]

        return self._calculate_architecture_score(file_paths, hexagonal_patterns)

    def _check_mvc_architecture(self, file_paths: list[str]) -> float:
        """
        Check if the codebase follows an MVC architecture.

        Args:
            file_paths: List of file paths in the codebase.

        Returns:
            A confidence score between 0 and 1.
        """
        # Look for typical MVC architecture directories
        mvc_patterns = [r"models", r"views", r"controllers", r"templates"]

        return self._calculate_architecture_score(file_paths, mvc_patterns)

    def _check_layered_architecture(self, file_paths: list[str]) -> float:
        """
        Check if the codebase follows a layered architecture.

        Args:
            file_paths: List of file paths in the codebase.

        Returns:
            A confidence score between 0 and 1.
        """
        # Look for typical layered architecture directories
        layered_patterns = [
            r"presentation",
            r"business",
            r"service",
            r"persistence",
            r"data",
            r"ui",
            r"api",
        ]

        return self._calculate_architecture_score(file_paths, layered_patterns)

    def _check_microservices_architecture(self, file_paths: list[str]) -> float:
        """
        Check if the codebase follows a microservices architecture.

        Args:
            file_paths: List of file paths in the codebase.

        Returns:
            A confidence score between 0 and 1.
        """
        # Look for typical microservices architecture patterns
        microservices_patterns = [
            r"services",
            r"api-gateway",
            r"service-registry",
            r"config-server",
            r"discovery",
        ]

        return self._calculate_architecture_score(file_paths, microservices_patterns)

    def _calculate_architecture_score(
        self, file_paths: list[str], patterns: list[str]
    ) -> float:
        """
        Calculate a confidence score for an architecture type based on matching patterns.

        Args:
            file_paths: List of file paths in the codebase.
            patterns: List of regex patterns to match against file paths.

        Returns:
            A confidence score between 0 and 1.
        """
        matches = 0
        total_patterns = len(patterns)

        for pattern in patterns:
            for file_path in file_paths:
                if re.search(pattern, file_path, re.IGNORECASE):
                    matches += 1
                    break

        # Calculate score based on the number of matched patterns
        if total_patterns == 0:
            return 0.0

        return min(1.0, matches / total_patterns)

    def _identify_layers(self, code_analysis: CodeAnalysis) -> dict[str, list[str]]:
        """
        Identify layers in the codebase based on directory structure.

        Args:
            code_analysis: The result of analyzing the codebase.

        Returns:
            A dictionary mapping layer names to components.
        """
        logger.info("Identifying layers")

        # Get all file paths
        file_paths = list(code_analysis.get_files().keys())

        # Extract top-level directories as potential layers
        potential_layers = set()
        for file_path in file_paths:
            try:
                relative_path = os.path.relpath(file_path, self.project_root)
                parts = relative_path.split(os.sep)

                # Skip very short paths
                if len(parts) < 2:
                    continue

                # For typical project structures, the first level directories are often layers
                potential_layer = parts[0]

                # If we're in a src directory, look at the next level
                if potential_layer == "src" and len(parts) >= 2:
                    potential_layer = parts[1]

                    # If the next level is the project name, look one level deeper
                    project_name = os.path.basename(self.project_root)
                    if potential_layer == project_name and len(parts) >= 3:
                        potential_layer = parts[2]

                # Skip common non-layer directories
                if potential_layer not in [
                    ".git",
                    ".idea",
                    ".vscode",
                    "__pycache__",
                    "venv",
                    "env",
                    ".env",
                    "node_modules",
                    "build",
                    "dist",
                ]:
                    potential_layers.add(potential_layer)
            except Exception as e:
                logger.warning(f"Error processing file path {file_path}: {str(e)}")
                continue

        # Create a dictionary mapping each layer to an empty list of components
        layers = {layer: [] for layer in potential_layers}

        # If no layers were detected, use some common architecture layers based on detected architecture type
        if not layers:
            architecture_type, _ = self._detect_architecture_type(code_analysis)

            if architecture_type == "Hexagonal":
                layers = {"domain": [], "application": [], "adapters": [], "ports": []}
            elif architecture_type == "MVC":
                layers = {"models": [], "views": [], "controllers": []}
            elif architecture_type == "Layered":
                layers = {"presentation": [], "business": [], "data": []}
            elif architecture_type == "Microservices":
                layers = {"services": [], "api-gateway": [], "common": []}
            else:
                # Default to a simple structure for unknown architecture
                layers = {"src": [], "tests": []}

        return layers

    def _analyze_layer_dependencies(
        self, code_analysis: CodeAnalysis, layers: dict[str, list[str]]
    ) -> dict[str, set[str]]:
        """
        Analyze dependencies between layers.

        Args:
            code_analysis: The result of analyzing the codebase.
            layers: Dictionary mapping layer names to components.

        Returns:
            A dictionary mapping each layer to the set of layers it depends on.
        """
        logger.info("Analyzing layer dependencies")

        layer_dependencies = {layer: set() for layer in layers.keys()}

        # Get the project name from the project root
        project_name = os.path.basename(self.project_root)

        # Analyze imports to determine layer dependencies
        for file_path, file_analysis in code_analysis.get_files().items():
            try:
                # Determine the source layer for this file
                source_layer = None
                relative_path = os.path.relpath(file_path, self.project_root)
                parts = relative_path.split(os.sep)

                # Skip very short paths
                if len(parts) < 2:
                    continue

                # For typical project structures, the first level directories are often layers
                potential_layer = parts[0]

                # If we're in a src directory, look at the next level
                if potential_layer == "src" and len(parts) >= 2:
                    potential_layer = parts[1]

                    # If the next level is the project name, look one level deeper
                    if potential_layer == project_name and len(parts) >= 3:
                        potential_layer = parts[2]

                # If this is a recognized layer, use it as the source layer
                if potential_layer in layers:
                    source_layer = potential_layer

                # If we couldn't determine the source layer, skip this file
                if not source_layer:
                    continue

                # Analyze imports to determine dependencies
                for import_info in file_analysis.get_imports():
                    import_name = import_info.get("name", "")
                    from_module = import_info.get("from_module", "")

                    # Try to determine the target layer from the import
                    target_layer = None

                    # Check if the import is from the project
                    if from_module and from_module.split(".")[0] == project_name:
                        module_parts = from_module.split(".")
                        if len(module_parts) >= 2:
                            potential_target = module_parts[1]
                            if potential_target in layers:
                                target_layer = potential_target

                    # If we couldn't determine the target layer from the module name,
                    # try to match it against the layer names
                    if not target_layer:
                        for layer in layers.keys():
                            if layer in from_module or layer in import_name:
                                target_layer = layer
                                break

                    # If we found a target layer and it's different from the source layer,
                    # add it to the dependencies
                    if target_layer and target_layer != source_layer:
                        layer_dependencies[source_layer].add(target_layer)
            except Exception as e:
                logger.warning(
                    f"Error analyzing dependencies for file {file_path}: {str(e)}"
                )
                continue

        return layer_dependencies

    def _check_architecture_violations(
        self, layer_dependencies: dict[str, set[str]], architecture_type: str
    ) -> list[ArchitectureViolation]:
        """
        Check for violations of the detected architecture.

        Args:
            layer_dependencies: Dictionary mapping each layer to the set of layers it depends on.
            architecture_type: The detected architecture type.

        Returns:
            A list of architecture violations.
        """
        logger.info(f"Checking for {architecture_type} architecture violations")

        violations: list[ArchitectureViolation] = []

        # Define allowed dependencies based on architecture type
        if architecture_type == "Hexagonal":
            # In a hexagonal architecture:
            # - Domain should not depend on any other layer
            # - Application can depend on domain
            # - Adapters can depend on application and domain
            # - Ports can depend on domain
            allowed_dependencies: dict[str, set[str]] = {
                "domain": set(),
                "application": {"domain"},
                "adapters": {"domain", "application", "ports"},
                "ports": {"domain"},
            }
        elif architecture_type == "MVC":
            # In an MVC architecture:
            # - Models should not depend on views or controllers
            # - Views can depend on models
            # - Controllers can depend on models and views
            allowed_dependencies = {
                "models": set(),
                "views": {"models"},
                "controllers": {"models", "views"},
            }
        elif architecture_type == "Layered":
            # In a layered architecture, dependencies should only flow downward:
            # - Presentation depends on business
            # - Business depends on data
            # - Data doesn't depend on other layers
            allowed_dependencies = {
                "presentation": {"business", "service"},
                "business": {"data", "persistence"},
                "service": {"data", "persistence"},
                "data": set(),
                "persistence": set(),
                "ui": {"presentation", "business", "service"},
                "api": {"business", "service", "data"},
            }
        elif architecture_type == "Microservices":
            # In a microservices architecture, services should be independent
            # Common modules can be used by services
            allowed_dependencies = {}
            for layer in layer_dependencies.keys():
                if layer == "common":
                    allowed_dependencies[layer] = set()
                else:
                    allowed_dependencies[layer] = {"common"}
        else:
            # For unknown architecture, we can't determine violations
            return []

        # Check for violations, but only for layers that have defined rules
        for layer, dependencies in layer_dependencies.items():
            if layer in allowed_dependencies:
                for dependency in dependencies:
                    if dependency not in allowed_dependencies[layer]:
                        violations.append(
                            {
                                "source_layer": layer,
                                "target_layer": dependency,
                                "description": f"Layer '{layer}' should not depend on layer '{dependency}' in {architecture_type} architecture",
                            }
                        )

        return violations

    def _analyze_code_quality(self, code_analysis: CodeAnalysis) -> CodeQualityInsights:
        """
        Analyze the code quality of the codebase.

        Args:
            code_analysis: The result of analyzing the codebase.

        Returns:
            A dictionary containing insights about code quality.
        """
        logger.info("Analyzing code quality")

        # Initialize counters
        total_files = 0
        files_with_docstrings = 0
        total_classes = 0
        classes_with_docstrings = 0
        total_functions = 0
        functions_with_docstrings = 0

        # Analyze each file
        for file_path, file_analysis in code_analysis.get_files().items():
            total_files += 1
            if file_analysis.get_docstring():
                files_with_docstrings += 1

            for class_info in file_analysis.get_classes():
                total_classes += 1
                if class_info.get("docstring"):
                    classes_with_docstrings += 1

            for function_info in file_analysis.get_functions():
                total_functions += 1
                if function_info.get("docstring"):
                    functions_with_docstrings += 1

        # Calculate percentages
        docstring_coverage: DocstringCoverage = {
            "files": files_with_docstrings / total_files if total_files > 0 else 0,
            "classes": (
                classes_with_docstrings / total_classes if total_classes > 0 else 0
            ),
            "functions": (
                functions_with_docstrings / total_functions
                if total_functions > 0
                else 0
            ),
        }

        return {
            "docstring_coverage": docstring_coverage,
            "total_files": total_files,
            "total_classes": total_classes,
            "total_functions": total_functions,
        }

    def _analyze_test_coverage(
        self, code_analysis: CodeAnalysis
    ) -> TestCoverageInsights:
        """
        Analyze the test coverage of the codebase.

        Args:
            code_analysis: The result of analyzing the codebase.

        Returns:
            A dictionary containing insights about test coverage.
        """
        logger.info("Analyzing test coverage")

        # Get all symbols from the codebase
        all_symbols = cast(
            dict[str, list[SymbolReference]], code_analysis.get_symbols()
        )

        # Find test directories and files
        tested_symbols: set[str] = set()
        test_dirs: list[str] = []

        # Common test directory names
        test_dir_names = ["tests", "test", "testing", "unittest", "pytest"]

        # Look for test directories in the project root
        for test_dir_name in test_dir_names:
            test_dir = os.path.join(self.project_root, test_dir_name)
            if os.path.exists(test_dir) and os.path.isdir(test_dir):
                test_dirs.append(test_dir)

        # If no test directories were found, look for test files directly
        if not test_dirs:
            for root, dirs, files in os.walk(self.project_root):
                for file in files:
                    if file.startswith("test_") and file.endswith(".py"):
                        test_dirs.append(root)
                        break

        # Analyze each test directory
        for test_dir in test_dirs:
            logger.info(f"Analyzing tests in {test_dir}")
            test_analysis = self.code_analyzer.analyze_directory(test_dir)

            # Extract tested symbols from test files
            for file_path, file_analysis in test_analysis.get_files().items():
                for import_info in file_analysis.get_imports():
                    import_details = cast(ImportInfo, import_info)
                    import_name = import_details.get("name", "")
                    from_module = import_details.get("from_module", "")

                    # Check if the import is from devsynth
                    if from_module and from_module.startswith("devsynth."):
                        # Add the imported symbols to the set of tested symbols
                        imported_names = import_details.get("imported_names", [])
                        for name in imported_names:
                            tested_symbols.add(f"{from_module}.{name}")
                    elif import_name and import_name.startswith("devsynth."):
                        tested_symbols.add(import_name)

        # Calculate test coverage
        total_symbols = len(all_symbols)
        tested_symbol_count = sum(
            1 for symbol in all_symbols if symbol in tested_symbols
        )
        coverage_percentage = (
            tested_symbol_count / total_symbols if total_symbols > 0 else 0
        )

        return {
            "total_symbols": total_symbols,
            "tested_symbols": tested_symbol_count,
            "coverage_percentage": coverage_percentage,
        }

    def _identify_improvement_opportunities(
        self,
        code_analysis: CodeAnalysis,
        architecture_insights: ArchitectureInsights,
        code_quality_insights: CodeQualityInsights,
        test_coverage_insights: TestCoverageInsights,
    ) -> list[ImprovementOpportunity]:
        """
        Identify opportunities for improving the codebase.

        Args:
            code_analysis: The result of analyzing the codebase.
            architecture_insights: Insights about the architecture.
            code_quality_insights: Insights about code quality.
            test_coverage_insights: Insights about test coverage.

        Returns:
            A list of improvement opportunities.
        """
        logger.info("Identifying improvement opportunities")

        opportunities: list[ImprovementOpportunity] = []

        # Check for architecture violations
        for violation in architecture_insights["architecture_violations"]:
            opportunities.append(
                {
                    "type": "architecture_violation",
                    "description": violation["description"],
                    "priority": "high",
                }
            )

        # Check for low docstring coverage
        docstring_coverage = code_quality_insights["docstring_coverage"]
        if docstring_coverage["files"] < 0.8:
            opportunities.append(
                {
                    "type": "low_docstring_coverage",
                    "description": f"Only {docstring_coverage['files'] * 100:.1f}% of files have docstrings",
                    "priority": "medium",
                }
            )

        if docstring_coverage["classes"] < 0.8:
            opportunities.append(
                {
                    "type": "low_docstring_coverage",
                    "description": f"Only {docstring_coverage['classes'] * 100:.1f}% of classes have docstrings",
                    "priority": "medium",
                }
            )

        if docstring_coverage["functions"] < 0.8:
            opportunities.append(
                {
                    "type": "low_docstring_coverage",
                    "description": f"Only {docstring_coverage['functions'] * 100:.1f}% of functions have docstrings",
                    "priority": "medium",
                }
            )

        # Check for low test coverage
        coverage_percentage = test_coverage_insights["coverage_percentage"]
        if coverage_percentage < 0.7:
            opportunities.append(
                {
                    "type": "low_test_coverage",
                    "description": f"Only {coverage_percentage * 100:.1f}% of symbols are covered by tests",
                    "priority": "high",
                }
            )

        return opportunities
