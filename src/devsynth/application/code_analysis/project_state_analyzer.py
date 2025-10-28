"""
Project State Analyzer for DevSynth.

This module provides functionality to analyze the state of a project,
including file indexing, language detection, architecture inference,
and consistency checking between requirements, specifications, and code.
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, TypedDict, Union

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError


class IndexedFileInfo(TypedDict):
    """Metadata captured for each indexed file."""

    path: str
    extension: str
    size: int
    last_modified: float


class LanguageStats(TypedDict):
    """Aggregated statistics for a detected language."""

    count: int
    percentage: float


class ArchitectureComponent(TypedDict):
    """Structural component inferred from the repository."""

    type: str
    path: str
    name: str


class ArchitectureModel(TypedDict):
    """Overall architecture inference including detected components."""

    type: str
    confidence: float
    components: list[ArchitectureComponent]


class RequirementRecord(TypedDict):
    """Structured representation of a requirement statement."""

    text: str
    section: str
    source_file: str


class SpecificationRecord(TypedDict):
    """Structured representation of a specification statement."""

    text: str
    section: str
    source_file: str


class RequirementSpecAlignment(TypedDict):
    """Alignment information between requirements and specifications."""

    total_requirements: int
    total_specifications: int
    matched_requirements: int
    unmatched_requirements: list[RequirementRecord]
    unmatched_specifications: list[SpecificationRecord]
    alignment_score: float


class SpecCodeAlignment(TypedDict):
    """Alignment information between specifications and implementation."""

    total_specifications: int
    implemented_specifications: int
    unimplemented_specifications: list[SpecificationRecord]
    implementation_score: float


class AnalysisIssue(TypedDict, total=False):
    """Issue discovered while analysing the project state."""

    severity: str
    type: str
    description: str
    details: list[RequirementRecord | SpecificationRecord]


class HealthReport(TypedDict):
    """Overall health summary for the analysed project."""

    project_path: str
    file_count: int
    languages: list[str]
    architecture: ArchitectureModel
    requirements_count: int
    specifications_count: int
    test_count: int
    code_count: int
    requirements_spec_alignment: RequirementSpecAlignment
    spec_code_alignment: SpecCodeAlignment
    health_score: float
    issues: list[AnalysisIssue]
    recommendations: list[str]


class ProjectStateSummary(TypedDict):
    """High-level summary returned by :class:`ProjectStateAnalyzer`."""

    files: dict[str, IndexedFileInfo]
    languages: dict[str, LanguageStats]
    architecture: ArchitectureModel
    components: list[ArchitectureComponent]
    health_report: HealthReport


def _create_unknown_architecture() -> ArchitectureModel:
    """Produce a fresh architecture placeholder."""

    return {"type": "Unknown", "confidence": 0.0, "components": []}


class ProjectStateAnalyzer:
    """
    Analyzes the state of a project to understand its structure, languages,
    architecture, and consistency between artifacts.
    """

    def __init__(self, project_path: str):
        """
        Initialize the project state analyzer.

        Args:
            project_path: Path to the project root directory
        """
        self.project_path = project_path
        self.files: dict[str, IndexedFileInfo] = {}
        # ``file_index`` mirrors ``files`` for backwards compatibility with
        # earlier call sites that accessed the attribute directly.
        self.file_index: dict[str, IndexedFileInfo] = self.files
        self.languages: dict[str, LanguageStats] = {}
        self.detected_languages: set[str] = set()
        architecture = _create_unknown_architecture()
        self.architecture: ArchitectureModel = architecture
        self.architecture_model: ArchitectureModel = architecture
        self.requirements_files: list[str] = []
        self.specification_files: list[str] = []
        self.test_files: list[str] = []
        self.code_files: list[str] = []
        self.documentation_files: list[str] = []
        self.config_files: list[str] = []

    def analyze(self) -> ProjectStateSummary:
        """
        Perform full project analysis and generate report.

        Returns:
            A dictionary containing the analysis results
        """
        logger.info(f"Starting project analysis for {self.project_path}")

        try:
            self._index_files()
            self._detect_languages()
            self._infer_architecture()
            req_spec_alignment = self._analyze_requirements_spec_alignment()
            spec_code_alignment = self._analyze_spec_code_alignment()

            health_report = self._generate_health_report(
                req_spec_alignment, spec_code_alignment
            )

            # Return the expected structure for the tests
            return {
                "files": self.files,
                "languages": self.languages,
                "architecture": self.architecture,
                "components": self.architecture["components"],
                "health_report": health_report,
            }
        except Exception as e:
            logger.error(f"ProjectStateAnalyzer.analyze failed: {e}")
            safe_files: dict[str, IndexedFileInfo] = {}
            safe_languages: dict[str, LanguageStats] = {}
            safe_components: list[ArchitectureComponent] = []
            safe_architecture: ArchitectureModel = {
                "type": "unknown",
                "confidence": 0.0,
                "components": safe_components,
            }
            empty_req_spec: RequirementSpecAlignment = {
                "total_requirements": 0,
                "total_specifications": 0,
                "matched_requirements": 0,
                "unmatched_requirements": [],
                "unmatched_specifications": [],
                "alignment_score": 0.0,
            }
            empty_spec_code: SpecCodeAlignment = {
                "total_specifications": 0,
                "implemented_specifications": 0,
                "unimplemented_specifications": [],
                "implementation_score": 0.0,
            }
            empty_health_report: HealthReport = {
                "project_path": self.project_path,
                "file_count": 0,
                "languages": [],
                "architecture": safe_architecture,
                "requirements_count": 0,
                "specifications_count": 0,
                "test_count": 0,
                "code_count": 0,
                "requirements_spec_alignment": empty_req_spec,
                "spec_code_alignment": empty_spec_code,
                "health_score": 0.0,
                "issues": [],
                "recommendations": [],
            }
            return {
                "files": safe_files,
                "languages": safe_languages,
                "architecture": safe_architecture,
                "components": safe_components,
                "health_report": empty_health_report,
            }

    def _index_files(self) -> None:
        """
        Scan and index all project files.
        """
        logger.info("Indexing project files")

        # File extensions to ignore
        ignore_extensions = {
            ".pyc",
            ".pyo",
            ".pyd",
            ".git",
            ".idea",
            ".vscode",
            "__pycache__",
            ".DS_Store",
        }

        # Directories to ignore
        ignore_dirs = {
            ".git",
            ".idea",
            ".vscode",
            "__pycache__",
            "venv",
            "env",
            ".env",
            "node_modules",
        }

        for root, dirs, files in os.walk(self.project_path):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_dirs]

            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.project_path)

                # Skip ignored files
                if any(file.endswith(ext) for ext in ignore_extensions) or any(
                    part in ignore_dirs for part in rel_path.split(os.sep)
                ):
                    continue

                # Get file extension
                _, ext = os.path.splitext(file)

                # Categorize file
                self._categorize_file(file_path, rel_path, ext)

                # Add to file index
                file_info: IndexedFileInfo = {
                    "path": file_path,
                    "extension": ext,
                    "size": os.path.getsize(file_path),
                    "last_modified": os.path.getmtime(file_path),
                }
                self.files[rel_path] = file_info

        # Set file_index to files for backward compatibility
        self.file_index = self.files

        logger.info(f"Indexed {len(self.files)} files")

    def _categorize_file(self, file_path: str, rel_path: str, ext: str) -> None:
        """
        Categorize a file based on its path and extension.

        Args:
            file_path: Absolute path to the file
            rel_path: Relative path from project root
            ext: File extension
        """
        # Check for requirements files
        if "requirement" in rel_path.lower() or rel_path.endswith("requirements.md"):
            self.requirements_files.append(rel_path)

        # Check for specification files
        elif "spec" in rel_path.lower() or rel_path.endswith("specs.md"):
            self.specification_files.append(rel_path)

        # Check for test files
        elif "test" in rel_path.lower() or rel_path.startswith("tests/"):
            self.test_files.append(rel_path)

        # Check for documentation files
        elif ext in [".md", ".rst", ".txt"] or "doc" in rel_path.lower():
            self.documentation_files.append(rel_path)

        # Check for configuration files
        elif (
            ext in [".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"]
            or "config" in rel_path.lower()
        ):
            self.config_files.append(rel_path)

        # Check for code files
        elif ext in [
            ".py",
            ".js",
            ".ts",
            ".java",
            ".c",
            ".cpp",
            ".go",
            ".rs",
            ".rb",
            ".php",
        ]:
            self.code_files.append(rel_path)

    def _detect_languages(self) -> None:
        """
        Detect programming languages used in the project.
        """
        logger.info("Detecting programming languages")

        # Map of file extensions to languages
        extension_to_language = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".java": "Java",
            ".c": "C",
            ".cpp": "C++",
            ".go": "Go",
            ".rs": "Rust",
            ".rb": "Ruby",
            ".php": "PHP",
            ".html": "HTML",
            ".css": "CSS",
            ".scss": "SCSS",
            ".sql": "SQL",
        }

        # Count files by language
        language_counts: dict[str, int] = {}
        self.detected_languages = set()

        for file_info in self.files.values():
            ext = file_info["extension"]
            if ext in extension_to_language:
                language = extension_to_language[ext]
                self.detected_languages.add(language)
                language_counts[language] = language_counts.get(language, 0) + 1

        # Store language information in the expected format
        total_files = len(self.files)
        languages: dict[str, LanguageStats] = {}
        for lang, count in language_counts.items():
            languages[lang] = {
                "count": count,
                "percentage": count / total_files if total_files > 0 else 0.0,
            }
        self.languages = languages

        logger.info(f"Detected languages: {', '.join(self.detected_languages)}")

    def _infer_architecture(self) -> None:
        """
        Infer the project architecture based on directory structure and file patterns.
        """
        logger.info("Inferring project architecture")

        # Check for common architecture patterns
        architecture_patterns: dict[str, float] = {
            "MVC": self._check_mvc_pattern(),
            "Hexagonal": self._check_hexagonal_pattern(),
            "Microservices": self._check_microservices_pattern(),
            "Layered": self._check_layered_pattern(),
            "Event-Driven": self._check_event_driven_pattern(),
        }

        # Select the architecture with the highest confidence
        architecture, confidence = max(
            architecture_patterns.items(), key=lambda x: x[1]
        )

        if confidence > 0.5:
            arch_data: ArchitectureModel = {
                "type": architecture,
                "confidence": confidence,
                "components": self._identify_components(architecture),
            }
            self.architecture = arch_data
            self.architecture_model = arch_data  # Set both attributes to the same value
            logger.info(
                f"Inferred architecture: {architecture} (confidence: {confidence:.2f})"
            )
        else:
            arch_data = _create_unknown_architecture()
            self.architecture = arch_data
            self.architecture_model = arch_data  # Set both attributes to the same value
            logger.info("Could not confidently infer architecture")

    def _check_mvc_pattern(self) -> float:
        """
        Check if the project follows the MVC pattern.

        Returns:
            Confidence score between 0 and 1
        """
        # Look for model, view, controller directories or files
        has_models = any("model" in path.lower() for path in self.files)
        has_views = any("view" in path.lower() for path in self.files)
        has_controllers = any("controller" in path.lower() for path in self.files)

        if has_models and has_views and has_controllers:
            return 0.9
        elif (
            (has_models and has_views)
            or (has_models and has_controllers)
            or (has_views and has_controllers)
        ):
            return 0.6
        elif has_models or has_views or has_controllers:
            return 0.3
        else:
            return 0.0

    def _check_hexagonal_pattern(self) -> float:
        """
        Check if the project follows the hexagonal (ports and adapters) pattern.

        Returns:
            Confidence score between 0 and 1
        """
        # Look for domain, application, adapters, ports directories
        has_domain = any("domain" in path.lower() for path in self.files)
        has_application = any("application" in path.lower() for path in self.files)
        has_adapters = any("adapter" in path.lower() for path in self.files)
        has_ports = any("port" in path.lower() for path in self.files)

        if has_domain and has_application and has_adapters and has_ports:
            return 0.9
        elif has_domain and (has_adapters or has_ports):
            return 0.7
        elif has_domain or has_adapters or has_ports:
            return 0.4
        else:
            return 0.0

    def _check_microservices_pattern(self) -> float:
        """
        Check if the project follows a microservices pattern.

        Returns:
            Confidence score between 0 and 1
        """
        # Look for multiple service directories, each with its own structure
        service_dirs = [
            d
            for d in os.listdir(self.project_path)
            if os.path.isdir(os.path.join(self.project_path, d))
            and ("service" in d.lower() or "api" in d.lower())
        ]

        # Check for Docker files, docker-compose, kubernetes configs
        has_docker = any(
            "dockerfile" in path.lower() or "docker-compose" in path.lower()
            for path in self.files
        )
        has_kubernetes = any(
            "kubernetes" in path.lower() or "k8s" in path.lower() for path in self.files
        )

        if len(service_dirs) >= 3 and (has_docker or has_kubernetes):
            return 0.9
        elif len(service_dirs) >= 2 or (
            len(service_dirs) >= 1 and (has_docker or has_kubernetes)
        ):
            return 0.6
        elif len(service_dirs) >= 1 or has_docker or has_kubernetes:
            return 0.3
        else:
            return 0.0

    def _check_layered_pattern(self) -> float:
        """
        Check if the project follows a layered architecture pattern.

        Returns:
            Confidence score between 0 and 1
        """
        # Look for common layer names
        layers = [
            "presentation",
            "ui",
            "service",
            "business",
            "data",
            "persistence",
            "repository",
            "infrastructure",
        ]
        found_layers = [
            layer
            for layer in layers
            if any(layer in path.lower() for path in self.files)
        ]

        if len(found_layers) >= 3:
            return 0.8
        elif len(found_layers) >= 2:
            return 0.5
        elif len(found_layers) >= 1:
            return 0.3
        else:
            return 0.0

    def _check_event_driven_pattern(self) -> float:
        """
        Check if the project follows an event-driven architecture pattern.

        Returns:
            Confidence score between 0 and 1
        """
        # Look for event-related terms
        event_terms = [
            "event",
            "message",
            "queue",
            "topic",
            "subscriber",
            "publisher",
            "consumer",
            "producer",
        ]
        found_terms = [
            term
            for term in event_terms
            if any(term in path.lower() for path in self.files)
        ]

        # Check for event-driven frameworks
        event_frameworks = [
            "kafka",
            "rabbitmq",
            "activemq",
            "nats",
            "eventbridge",
            "pubsub",
        ]
        has_frameworks = any(
            framework in " ".join(self.files.keys()).lower()
            for framework in event_frameworks
        )

        if len(found_terms) >= 3 and has_frameworks:
            return 0.9
        elif len(found_terms) >= 2 or has_frameworks:
            return 0.6
        elif len(found_terms) >= 1:
            return 0.3
        else:
            return 0.0

    def _identify_components(self, architecture: str) -> list[ArchitectureComponent]:
        """
        Identify components based on the inferred architecture.

        Args:
            architecture: The inferred architecture type

        Returns:
            List of component dictionaries
        """
        components: list[ArchitectureComponent] = []

        if architecture == "Hexagonal":
            # Identify domain entities
            domain_files = [f for f in self.code_files if "domain" in f.lower()]
            for file in domain_files:
                components.append(
                    {
                        "type": "Domain Entity",
                        "path": file,
                        "name": os.path.basename(file).split(".")[0],
                    }
                )

            # Identify ports
            port_files = [f for f in self.code_files if "port" in f.lower()]
            for file in port_files:
                components.append(
                    {
                        "type": "Port",
                        "path": file,
                        "name": os.path.basename(file).split(".")[0],
                    }
                )

            # Identify adapters
            adapter_files = [f for f in self.code_files if "adapter" in f.lower()]
            for file in adapter_files:
                components.append(
                    {
                        "type": "Adapter",
                        "path": file,
                        "name": os.path.basename(file).split(".")[0],
                    }
                )

        elif architecture == "MVC":
            # Identify models
            model_files = [f for f in self.code_files if "model" in f.lower()]
            for file in model_files:
                components.append(
                    {
                        "type": "Model",
                        "path": file,
                        "name": os.path.basename(file).split(".")[0],
                    }
                )

            # Identify views
            view_files = [f for f in self.code_files if "view" in f.lower()]
            for file in view_files:
                components.append(
                    {
                        "type": "View",
                        "path": file,
                        "name": os.path.basename(file).split(".")[0],
                    }
                )

            # Identify controllers
            controller_files = [f for f in self.code_files if "controller" in f.lower()]
            for file in controller_files:
                components.append(
                    {
                        "type": "Controller",
                        "path": file,
                        "name": os.path.basename(file).split(".")[0],
                    }
                )

        # Add more architecture-specific component identification as needed

        return components

    def _analyze_requirements_spec_alignment(self) -> RequirementSpecAlignment:
        """
        Analyze alignment between requirements and specifications.

        Returns:
            Dictionary with alignment analysis results
        """
        logger.info("Analyzing requirements-specification alignment")

        alignment_results: RequirementSpecAlignment = {
            "total_requirements": 0,
            "total_specifications": 0,
            "matched_requirements": 0,
            "unmatched_requirements": [],
            "unmatched_specifications": [],
            "alignment_score": 0.0,
        }

        # Skip if no requirements or specifications
        if not self.requirements_files or not self.specification_files:
            logger.info("Skipping requirements-specification alignment: missing files")
            return alignment_results

        # Extract requirements
        requirements = self._extract_requirements()
        alignment_results["total_requirements"] = len(requirements)

        # Extract specifications
        specifications = self._extract_specifications()
        alignment_results["total_specifications"] = len(specifications)

        # Match requirements to specifications
        matched_reqs: list[RequirementRecord] = []
        for req in requirements:
            matched = False
            for spec in specifications:
                if self._is_requirement_matched_by_spec(req, spec):
                    matched = True
                    break

            if matched:
                matched_reqs.append(req)
            else:
                alignment_results["unmatched_requirements"].append(req)

        alignment_results["matched_requirements"] = len(matched_reqs)

        # Find specifications without matching requirements
        for spec in specifications:
            matched = False
            for req in requirements:
                if self._is_requirement_matched_by_spec(req, spec):
                    matched = True
                    break

            if not matched:
                alignment_results["unmatched_specifications"].append(spec)

        # Calculate alignment score
        if alignment_results["total_requirements"] > 0:
            alignment_results["alignment_score"] = (
                alignment_results["matched_requirements"]
                / alignment_results["total_requirements"]
            )

        logger.info(
            f"Requirements-specification alignment score: {alignment_results['alignment_score']:.2f}"
        )
        return alignment_results

    def _extract_requirements(self) -> list[RequirementRecord]:
        """
        Extract requirements from requirements files.

        Returns:
            List of requirement dictionaries
        """
        requirements: list[RequirementRecord] = []

        for req_file in self.requirements_files:
            try:
                with open(os.path.join(self.project_path, req_file)) as f:
                    content = f.read()

                # Simple extraction of requirements (can be enhanced with NLP)
                # Look for bullet points, numbered lists, or sections
                lines = content.split("\n")
                current_section = "General"

                for line in lines:
                    line = line.strip()

                    # Check for section headers
                    if line.startswith("# "):
                        current_section = line[2:].strip()
                        continue
                    elif line.startswith("## "):
                        current_section = line[3:].strip()
                        continue

                    # Check for requirement patterns
                    req_pattern = re.match(r"^[-*]|\d+\.\s+(.+)$", line)
                    if req_pattern:
                        req_text = req_pattern.group(1).strip()
                        if req_text:
                            requirements.append(
                                {
                                    "text": req_text,
                                    "section": current_section,
                                    "source_file": req_file,
                                }
                            )
            except Exception as e:
                logger.error(f"Error extracting requirements from {req_file}: {str(e)}")

        return requirements

    def _extract_specifications(self) -> list[SpecificationRecord]:
        """
        Extract specifications from specification files.

        Returns:
            List of specification dictionaries
        """
        specifications: list[SpecificationRecord] = []

        for spec_file in self.specification_files:
            try:
                with open(os.path.join(self.project_path, spec_file)) as f:
                    content = f.read()

                # Simple extraction of specifications (can be enhanced with NLP)
                # Look for bullet points, numbered lists, or sections
                lines = content.split("\n")
                current_section = "General"

                for line in lines:
                    line = line.strip()

                    # Check for section headers
                    if line.startswith("# "):
                        current_section = line[2:].strip()
                        continue
                    elif line.startswith("## "):
                        current_section = line[3:].strip()
                        continue

                    # Check for specification patterns
                    spec_pattern = re.match(r"^[-*]|\d+\.\s+(.+)$", line)
                    if spec_pattern:
                        spec_text = spec_pattern.group(1).strip()
                        if spec_text:
                            specifications.append(
                                {
                                    "text": spec_text,
                                    "section": current_section,
                                    "source_file": spec_file,
                                }
                            )
            except Exception as e:
                logger.error(
                    f"Error extracting specifications from {spec_file}: {str(e)}"
                )

        return specifications

    def _is_requirement_matched_by_spec(
        self, requirement: RequirementRecord, specification: SpecificationRecord
    ) -> bool:
        """
        Check if a requirement is matched by a specification.

        Args:
            requirement: Requirement dictionary
            specification: Specification dictionary

        Returns:
            True if the requirement is matched by the specification
        """
        # Simple matching based on text similarity (can be enhanced with NLP)
        req_text = requirement["text"].lower()
        spec_text = specification["text"].lower()

        # Check for direct keyword matches
        req_keywords = set(re.findall(r"\b\w+\b", req_text))
        spec_keywords = set(re.findall(r"\b\w+\b", spec_text))

        # Calculate keyword overlap
        if len(req_keywords) > 0:
            overlap = len(req_keywords.intersection(spec_keywords)) / len(req_keywords)
            return overlap > 0.5

        return False

    def _analyze_spec_code_alignment(self) -> SpecCodeAlignment:
        """
        Analyze alignment between specifications and code.

        Returns:
            Dictionary with alignment analysis results
        """
        logger.info("Analyzing specification-code alignment")

        alignment_results: SpecCodeAlignment = {
            "total_specifications": 0,
            "implemented_specifications": 0,
            "unimplemented_specifications": [],
            "implementation_score": 0.0,
        }

        # Skip if no specifications
        if not self.specification_files:
            logger.info("Skipping specification-code alignment: no specification files")
            return alignment_results

        # Extract specifications
        specifications = self._extract_specifications()
        alignment_results["total_specifications"] = len(specifications)

        # For each specification, check if it's implemented in code
        implemented_specs: list[SpecificationRecord] = []
        for spec in specifications:
            if self._is_specification_implemented(spec):
                implemented_specs.append(spec)
            else:
                alignment_results["unimplemented_specifications"].append(spec)

        alignment_results["implemented_specifications"] = len(implemented_specs)

        # Calculate implementation score
        if alignment_results["total_specifications"] > 0:
            alignment_results["implementation_score"] = (
                alignment_results["implemented_specifications"]
                / alignment_results["total_specifications"]
            )

        logger.info(
            f"Specification-code implementation score: {alignment_results['implementation_score']:.2f}"
        )
        return alignment_results

    def _is_specification_implemented(self, specification: SpecificationRecord) -> bool:
        """
        Check if a specification is implemented in code.

        Args:
            specification: Specification dictionary

        Returns:
            True if the specification is implemented
        """
        # Simple implementation check based on keyword matching (can be enhanced with AST parsing)
        spec_text = specification["text"].lower()

        # Extract key terms from the specification
        key_terms = set(re.findall(r"\b\w+\b", spec_text))
        key_terms = {
            term for term in key_terms if len(term) > 3
        }  # Filter out short words

        # Check if key terms appear in code files
        for code_file in self.code_files:
            try:
                with open(os.path.join(self.project_path, code_file)) as f:
                    content = f.read().lower()

                # Count how many key terms appear in the code
                found_terms = sum(1 for term in key_terms if term in content)

                # If more than half of the key terms are found, consider it implemented
                if found_terms > len(key_terms) / 2:
                    return True
            except Exception as e:
                logger.error(f"Error checking implementation in {code_file}: {str(e)}")

        return False

    def _generate_health_report(
        self,
        req_spec_alignment: RequirementSpecAlignment,
        spec_code_alignment: SpecCodeAlignment,
    ) -> HealthReport:
        """
        Generate a project health report.

        Args:
            req_spec_alignment: Requirements-specification alignment results
            spec_code_alignment: Specification-code alignment results

        Returns:
            Dictionary containing the health report
        """
        logger.info("Generating project health report")

        # Calculate overall health score
        health_score = 0.0
        factors = 0

        if req_spec_alignment["total_requirements"] > 0:
            health_score += req_spec_alignment["alignment_score"]
            factors += 1

        if spec_code_alignment["total_specifications"] > 0:
            health_score += spec_code_alignment["implementation_score"]
            factors += 1

        if factors > 0:
            health_score /= factors

        # Generate report
        report: HealthReport = {
            "project_path": self.project_path,
            "file_count": len(self.files),
            "languages": list(self.detected_languages),
            "architecture": self.architecture,
            "requirements_count": len(self.requirements_files),
            "specifications_count": len(self.specification_files),
            "test_count": len(self.test_files),
            "code_count": len(self.code_files),
            "requirements_spec_alignment": req_spec_alignment,
            "spec_code_alignment": spec_code_alignment,
            "health_score": health_score,
            "issues": self._identify_issues(req_spec_alignment, spec_code_alignment),
            "recommendations": self._generate_recommendations(
                req_spec_alignment, spec_code_alignment
            ),
        }

        logger.info(f"Project health score: {health_score:.2f}")
        return report

    def _identify_issues(
        self,
        req_spec_alignment: RequirementSpecAlignment,
        spec_code_alignment: SpecCodeAlignment,
    ) -> list[AnalysisIssue]:
        """
        Identify issues in the project.

        Args:
            req_spec_alignment: Requirements-specification alignment results
            spec_code_alignment: Specification-code alignment results

        Returns:
            List of issue dictionaries
        """
        issues: list[AnalysisIssue] = []

        # Check for missing requirements files
        if not self.requirements_files:
            issues.append(
                {
                    "severity": "high",
                    "type": "missing_requirements",
                    "description": "No requirements files found in the project",
                }
            )

        # Check for missing specification files
        if not self.specification_files:
            issues.append(
                {
                    "severity": "high",
                    "type": "missing_specifications",
                    "description": "No specification files found in the project",
                }
            )

        # Check for missing test files
        if not self.test_files:
            issues.append(
                {
                    "severity": "medium",
                    "type": "missing_tests",
                    "description": "No test files found in the project",
                }
            )

        # Check for unmatched requirements
        if req_spec_alignment["unmatched_requirements"]:
            issues.append(
                {
                    "severity": "high",
                    "type": "unmatched_requirements",
                    "description": f"{len(req_spec_alignment['unmatched_requirements'])} requirements not matched by specifications",
                    "details": req_spec_alignment["unmatched_requirements"],
                }
            )

        # Check for unimplemented specifications
        if spec_code_alignment["unimplemented_specifications"]:
            issues.append(
                {
                    "severity": "medium",
                    "type": "unimplemented_specifications",
                    "description": f"{len(spec_code_alignment['unimplemented_specifications'])} specifications not implemented in code",
                    "details": spec_code_alignment["unimplemented_specifications"],
                }
            )

        return issues

    def _generate_recommendations(
        self,
        req_spec_alignment: RequirementSpecAlignment,
        spec_code_alignment: SpecCodeAlignment,
    ) -> list[str]:
        """
        Generate recommendations based on the analysis.

        Args:
            req_spec_alignment: Requirements-specification alignment results
            spec_code_alignment: Specification-code alignment results

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Recommendations for missing files
        if not self.requirements_files:
            recommendations.append(
                "Create requirements documentation to clearly define project goals"
            )

        if not self.specification_files:
            recommendations.append(
                "Develop specifications based on requirements to guide implementation"
            )

        if not self.test_files:
            recommendations.append(
                "Add tests to ensure code quality and prevent regressions"
            )

        # Recommendations for alignment issues
        if req_spec_alignment["unmatched_requirements"]:
            recommendations.append(
                f"Update specifications to address {len(req_spec_alignment['unmatched_requirements'])} unmatched requirements"
            )

        if spec_code_alignment["unimplemented_specifications"]:
            recommendations.append(
                f"Implement code for {len(spec_code_alignment['unimplemented_specifications'])} unimplemented specifications"
            )

        # Architecture recommendations
        if self.architecture and self.architecture["type"] != "Unknown":
            if self.architecture["confidence"] < 0.7:
                recommendations.append(
                    f"Consider clarifying the {self.architecture['type']} architecture by reorganizing files and directories"
                )
        else:
            recommendations.append(
                "Consider adopting a clear architectural pattern to improve code organization"
            )

        # Language recommendations
        if len(self.detected_languages) > 3:
            recommendations.append(
                "Consider consolidating the number of programming languages used in the project"
            )

        # Test recommendations
        if len(self.test_files) < len(self.code_files) * 0.5:
            recommendations.append(
                "Increase test coverage to improve code quality and maintainability"
            )

        return recommendations
