"""
Dialectical Audit System

This module provides comprehensive cross-referencing between documentation, code, and tests
to identify inconsistencies and generate questions requiring dialectical review.

The system implements DevSynth's dialectical philosophy by:
- Cross-referencing features across all artifacts (docs, code, tests)
- Identifying inconsistencies and gaps in implementation
- Generating questions that require structured critical thinking
- Providing evidence-based analysis for decision-making

Key features:
- Cross-artifact feature extraction and comparison
- Inconsistency detection with severity classification
- Question generation for dialectical review
- Integration with DevSynth's memory system for persistent audit data
- Automated audit logging and reporting
"""

import json
import os
import re
from dataclasses import dataclass, field  # type: ignore[attr-defined]
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, cast

from devsynth.ports.memory_port import MemoryPort
from devsynth.domain.models.memory import MemoryType


@dataclass
class AuditQuestion:
    """Represents a question requiring dialectical review."""

    question: str
    feature_name: str
    inconsistency_type: str
    severity: str
    artifacts: list[str]
    evidence: dict[str, Any]
    suggestion: str
    requires_review: bool = True


@dataclass
class ArtifactFeature:
    """Features found in a specific artifact."""

    artifact_path: str
    artifact_type: str  # docs, code, tests
    features: set[str]
    feature_locations: dict[str, int]  # feature -> line number


@dataclass
class DialecticalAuditResult:
    """Results of a dialectical audit."""

    timestamp: datetime
    project_path: str
    total_features_found: int
    inconsistencies_found: int
    questions_generated: list[AuditQuestion]
    coverage_analysis: dict[str, dict[str, float]]
    feature_matrix: dict[str, dict[str, bool]]
    audit_summary: dict[str, Any]


class DialecticalAuditSystem:
    """
    Cross-references documentation, code, and tests for conflicting statements.

    This system implements dialectical reasoning by analyzing features across multiple
    artifacts and identifying inconsistencies that require structured critical thinking
    to resolve. It generates questions for review and provides evidence-based analysis.

    The audit looks for:
    - Features documented but not implemented
    - Features implemented but not documented
    - Features tested but not documented or implemented
    - Inconsistencies in feature descriptions across artifacts
    """

    def __init__(self, memory_port: MemoryPort | None = None):
        """Initialize the dialectical audit system."""
        self.memory_port = memory_port
        self.audit_log_path = Path.home() / ".devsynth" / "dialectical_audit.log"
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)

        # Manual mapping of source locations to feature names
        # Some features are implemented in code but not annotated with # Feature: comments
        self.code_feature_map = {
            "src/devsynth/interface/webui.py": {
                "diagnostics_page": "WebUI Diagnostics Page",
                "metrics_page": "WebUI Metrics Page",
                "configuration_page": "WebUI Configuration Page",
            },
            "src/devsynth/application/agents/wsde_team_coordinator.py": {
                "wsde_collaboration": "WSDE Team Collaboration",
                "agent_coordination": "Agent Coordination",
                "consensus_building": "Consensus Building",
            },
        }

        # Feature extraction patterns
        self.feature_patterns = [
            r"^Feature:\s*(.+)",  # BDD feature files
            r"#\s*Feature:\s*(.+)",  # Code comments
            r"Feature:\s*(.+)",  # Documentation
            r"^\s*-\s*(.+?)\s*:\s*",  # List items that might be features
        ]

    def run_dialectical_audit(
        self,
        project_path: str = ".",
        include_docs: bool = True,
        include_code: bool = True,
        include_tests: bool = True,
    ) -> DialecticalAuditResult:
        """
        Run a comprehensive dialectical audit.

        Args:
            project_path: Path to the project to audit
            include_docs: Whether to include documentation in audit
            include_code: Whether to include code in audit
            include_tests: Whether to include tests in audit

        Returns:
            DialecticalAuditResult with audit findings
        """
        start_time = datetime.now()
        project_root = Path(project_path).resolve()

        # Extract features from all artifact types
        doc_features = set()
        code_features = set()
        test_features = set()

        if include_docs:
            doc_features = self.extract_features_from_docs(project_root / "docs")

        if include_code:
            code_features = self.extract_features_from_code(project_root / "src")

        if include_tests:
            test_features = self.extract_features_from_tests(project_root / "tests")

        # Analyze coverage and generate questions
        all_features = doc_features | code_features | test_features

        # Build feature matrix
        feature_matrix = {}
        for feature in all_features:
            feature_matrix[feature] = {
                "docs": feature in doc_features,
                "code": feature in code_features,
                "tests": feature in test_features,
            }

        # Generate questions for inconsistencies
        questions = self.generate_audit_questions(feature_matrix, project_root)

        # Calculate coverage analysis
        coverage_analysis = self.analyze_coverage(feature_matrix)

        # Create audit result
        result = DialecticalAuditResult(
            timestamp=start_time,
            project_path=str(project_root),
            total_features_found=len(all_features),
            inconsistencies_found=len(questions),
            questions_generated=questions,
            coverage_analysis=coverage_analysis,
            feature_matrix={f: m for f, m in feature_matrix.items()},
            audit_summary=self._generate_audit_summary(questions, coverage_analysis),
        )

        # Log audit results
        self.log_audit_results([q.question for q in questions])

        # Store in memory if available
        if self.memory_port:
            self._store_audit_results(result)

        return result

    def extract_features_from_docs(self, docs_dir: Path) -> set[str]:
        """Extract feature references from documentation."""
        features: set[str] = set()

        if not docs_dir.exists():
            return features

        for path in docs_dir.rglob("*.md"):
            try:
                content = path.read_text(encoding="utf-8")
                features.update(
                    self._extract_features_from_text(content, str(path), "docs")
                )
            except (UnicodeDecodeError, OSError):
                continue

        return features

    def extract_features_from_tests(self, tests_dir: Path) -> set[str]:
        """Extract feature references from test files."""
        features: set[str] = set()

        if not tests_dir.exists():
            return features

        # Extract from BDD feature files
        for path in tests_dir.rglob("*.feature"):
            try:
                content = path.read_text(encoding="utf-8")
                for line in content.splitlines():
                    if line.startswith("Feature:"):
                        feature_name = line.split("Feature:", 1)[1].strip()
                        features.add(feature_name)
                        break
            except (UnicodeDecodeError, OSError):
                continue

        # Extract from Python test files
        for path in tests_dir.rglob("*.py"):
            try:
                content = path.read_text(encoding="utf-8")
                features.update(
                    self._extract_features_from_text(content, str(path), "tests")
                )
            except (UnicodeDecodeError, OSError):
                continue

        return features

    def extract_features_from_code(self, code_dir: Path) -> set[str]:
        """Extract feature references from code comments."""
        features: set[str] = set()

        if not code_dir.exists():
            return features

        for path in code_dir.rglob("*.py"):
            try:
                content = path.read_text(encoding="utf-8")
                features.update(
                    self._extract_features_from_text(content, str(path), "code")
                )

                # Check for manual feature mappings
                rel_path = str(path.relative_to(code_dir.parent.parent))
                if rel_path in self.code_feature_map:
                    for func_name, feature_name in self.code_feature_map[
                        rel_path
                    ].items():
                        if re.search(rf"def\s+{re.escape(func_name)}\s*\(", content):
                            features.add(feature_name)

            except (UnicodeDecodeError, OSError):
                continue

        return features

    def _extract_features_from_text(
        self, content: str, source_path: str, artifact_type: str
    ) -> set[str]:
        """Extract features from text content."""
        features = set()

        lines = content.splitlines()

        for line_num, line in enumerate(lines, 1):
            # Skip comments in code files unless they explicitly mention features
            if artifact_type == "code" and line.strip().startswith("#"):
                if "Feature:" in line:
                    match = re.search(r"#\s*Feature:\s*(.+)", line)
                    if match:
                        features.add(match.group(1).strip())
            elif artifact_type in ["docs", "tests"]:
                # Check all feature patterns in docs and tests
                for pattern in self.feature_patterns:
                    match = re.match(pattern, line.strip())
                    if match:
                        feature_text = match.group(1).strip()
                        # Clean up feature text
                        feature_text = re.sub(r"[^\w\s\-_]", "", feature_text)
                        if len(feature_text) > 3:  # Avoid very short matches
                            features.add(feature_text)

        return features

    def generate_audit_questions(
        self, feature_matrix: dict[str, dict[str, bool]], project_root: Path
    ) -> list[AuditQuestion]:
        """Generate questions requiring dialectical review."""
        questions = []

        for feature, coverage in feature_matrix.items():
            # Check for inconsistencies in feature coverage
            has_docs = coverage.get("docs", False)
            has_code = coverage.get("code", False)
            has_tests = coverage.get("tests", False)

            # Generate questions based on coverage patterns
            if has_tests and not has_docs:
                questions.append(
                    AuditQuestion(
                        question=f"Feature '{feature}' has tests but is not documented.",
                        feature_name=feature,
                        inconsistency_type="missing_documentation",
                        severity="medium",
                        artifacts=["tests"],
                        evidence={"tests_only": True, "missing_docs": True},
                        suggestion="Add documentation for this feature or verify if it's still needed",
                    )
                )

            elif has_docs and not has_tests:
                questions.append(
                    AuditQuestion(
                        question=f"Feature '{feature}' is documented but has no corresponding tests.",
                        feature_name=feature,
                        inconsistency_type="missing_tests",
                        severity="high",
                        artifacts=["docs"],
                        evidence={"docs_only": True, "missing_tests": True},
                        suggestion="Add tests for this documented feature or remove documentation if feature is deprecated",
                    )
                )

            elif has_code and not has_docs and not has_tests:
                questions.append(
                    AuditQuestion(
                        question=f"Feature '{feature}' is implemented in code but not documented or tested.",
                        feature_name=feature,
                        inconsistency_type="missing_docs_and_tests",
                        severity="high",
                        artifacts=["code"],
                        evidence={
                            "code_only": True,
                            "missing_docs": True,
                            "missing_tests": True,
                        },
                        suggestion="Add comprehensive documentation and tests for this implemented feature",
                    )
                )

            elif not has_code and not has_docs and not has_tests:
                # This might be a false positive from pattern matching
                questions.append(
                    AuditQuestion(
                        question=f"Feature '{feature}' appears in multiple artifacts but implementation unclear.",
                        feature_name=feature,
                        inconsistency_type="unclear_implementation",
                        severity="low",
                        artifacts=[],
                        evidence={"ambiguous": True},
                        suggestion="Verify if this is a valid feature or remove references",
                    )
                )

        return questions

    def analyze_coverage(
        self, feature_matrix: dict[str, dict[str, bool]]
    ) -> dict[str, dict[str, float]]:
        """Analyze feature coverage across artifact types."""
        coverage = {
            "docs": {"covered": 0, "total": 0, "percentage": 0.0},
            "code": {"covered": 0, "total": 0, "percentage": 0.0},
            "tests": {"covered": 0, "total": 0, "percentage": 0.0},
        }

        total_features = len(feature_matrix)

        for feature, artifacts in feature_matrix.items():
            coverage["docs"]["total"] = total_features
            coverage["code"]["total"] = total_features
            coverage["tests"]["total"] = total_features

            if artifacts.get("docs", False):
                coverage["docs"]["covered"] += 1

            if artifacts.get("code", False):
                coverage["code"]["covered"] += 1

            if artifacts.get("tests", False):
                coverage["tests"]["covered"] += 1

        # Calculate percentages
        for artifact_type in coverage:
            if coverage[artifact_type]["total"] > 0:
                coverage[artifact_type]["percentage"] = (
                    coverage[artifact_type]["covered"]
                    / coverage[artifact_type]["total"]
                ) * 100

        return coverage

    def log_audit_results(self, questions: list[str]) -> None:
        """Log audit results for review."""
        try:
            # Load existing log or create new one
            if self.audit_log_path.exists():
                with open(self.audit_log_path) as f:
                    log_data = json.load(f)
            else:
                log_data = {"questions": [], "resolved": []}

            # Add new questions
            log_data["questions"].extend(questions)
            log_data["last_audit"] = datetime.now().isoformat()

            # Save updated log
            with open(self.audit_log_path, "w") as f:
                json.dump(log_data, f, indent=2)

        except (json.JSONDecodeError, OSError):
            # If logging fails, create a simple log
            try:
                with open(self.audit_log_path, "w") as f:
                    json.dump(
                        {
                            "questions": questions,
                            "resolved": [],
                            "last_audit": datetime.now().isoformat(),
                        },
                        f,
                        indent=2,
                    )
            except OSError:
                pass

    def get_audit_history(self) -> dict[str, Any]:
        """Get audit history from log file."""
        try:
            if self.audit_log_path.exists():
                with open(self.audit_log_path) as f:
                    return cast(dict[str, Any], json.load(f))
            else:
                return {"questions": [], "resolved": [], "last_audit": None}
        except (json.JSONDecodeError, OSError):
            return {"questions": [], "resolved": [], "last_audit": None}

    def resolve_question(self, question_text: str, resolution: str) -> None:
        """Mark a question as resolved with explanation."""
        try:
            log_data = self.get_audit_history()

            # Move question from questions to resolved
            if question_text in log_data["questions"]:
                log_data["questions"].remove(question_text)
                log_data["resolved"].append(
                    {
                        "question": question_text,
                        "resolution": resolution,
                        "resolved_at": datetime.now().isoformat(),
                    }
                )

            # Save updated log
            with open(self.audit_log_path, "w") as f:
                json.dump(log_data, f, indent=2)

        except (json.JSONDecodeError, OSError):
            pass

    def _generate_audit_summary(
        self,
        questions: list[AuditQuestion],
        coverage_analysis: dict[str, dict[str, float]],
    ) -> dict[str, Any]:
        """Generate audit summary."""
        # Count questions by type and severity
        by_type: dict[str, int] = {}
        by_severity = {"high": 0, "medium": 0, "low": 0}

        for question in questions:
            by_type[question.inconsistency_type] = (
                by_type.get(question.inconsistency_type, 0) + 1
            )
            by_severity[question.severity] += 1

        # Calculate overall health score
        total_possible = len(questions) + sum(
            coverage_analysis[artifact]["covered"] for artifact in coverage_analysis
        )
        if total_possible > 0:
            health_score = (
                sum(
                    coverage_analysis[artifact]["covered"]
                    for artifact in coverage_analysis
                )
                / total_possible
            ) * 100
        else:
            health_score = 100.0

        return {
            "total_questions": len(questions),
            "questions_by_type": by_type,
            "questions_by_severity": by_severity,
            "health_score": health_score,
            "coverage_percentages": {
                artifact: coverage["percentage"]
                for artifact, coverage in coverage_analysis.items()
            },
        }

    def _store_audit_results(self, result: DialecticalAuditResult) -> None:
        """Store audit results in memory system."""
        if not self.memory_port:
            return

        try:
            content = {
                "timestamp": result.timestamp.isoformat(),
                "total_features": result.total_features_found,
                "inconsistencies": result.inconsistencies_found,
                "questions": [q.question for q in result.questions_generated],
                "coverage_analysis": result.coverage_analysis,
                "health_score": result.audit_summary["health_score"],
            }
            self.memory_port.store_memory(
                content=content,
                memory_type=MemoryType.DIALECTICAL_REASONING,
                metadata={
                    "type": "dialectical_audit",
                    "project_path": result.project_path,
                    "key": "dialectical_audit_latest"
                },
            )

        except Exception:
            # Memory storage failed, but don't fail the operation
            pass

    def validate_feature_consistency(
        self, feature_name: str, project_root: Path
    ) -> dict[str, Any]:
        """
        Validate consistency of a specific feature across all artifacts.

        Args:
            feature_name: Name of the feature to validate
            project_root: Root path of the project

        Returns:
            Consistency validation results
        """
        # Search for feature in all artifacts
        docs_locations = self._find_feature_in_docs(feature_name, project_root / "docs")
        code_locations = self._find_feature_in_code(feature_name, project_root / "src")
        test_locations = self._find_feature_in_tests(
            feature_name, project_root / "tests"
        )

        # Analyze consistency
        consistency_issues = []

        # Check if feature exists in all expected places
        if not docs_locations:
            consistency_issues.append("Feature not documented")

        if not code_locations:
            consistency_issues.append("Feature not implemented")

        if not test_locations:
            consistency_issues.append("Feature not tested")

        # Check for version consistency
        version_issues = self._check_version_consistency(
            feature_name, docs_locations, code_locations, test_locations
        )
        consistency_issues.extend(version_issues)

        return {
            "feature_name": feature_name,
            "docs_locations": docs_locations,
            "code_locations": code_locations,
            "test_locations": test_locations,
            "consistency_issues": consistency_issues,
            "overall_consistent": len(consistency_issues) == 0,
        }

    def _find_feature_in_docs(self, feature_name: str, docs_dir: Path) -> list[str]:
        """Find feature in documentation."""
        locations: list[str] = []

        if not docs_dir.exists():
            return locations

        for path in docs_dir.rglob("*.md"):
            try:
                content = path.read_text(encoding="utf-8")
                if feature_name.lower() in content.lower():
                    # Find specific line numbers
                    for line_num, line in enumerate(content.splitlines(), 1):
                        if feature_name.lower() in line.lower():
                            locations.append(f"{path}:{line_num}")
            except (UnicodeDecodeError, OSError):
                continue

        return locations

    def _find_feature_in_code(self, feature_name: str, code_dir: Path) -> list[str]:
        """Find feature in code."""
        locations: list[str] = []

        if not code_dir.exists():
            return locations

        for path in code_dir.rglob("*.py"):
            try:
                content = path.read_text(encoding="utf-8")
                if feature_name.lower() in content.lower():
                    # Find specific line numbers
                    for line_num, line in enumerate(content.splitlines(), 1):
                        if feature_name.lower() in line.lower():
                            locations.append(f"{path}:{line_num}")
            except (UnicodeDecodeError, OSError):
                continue

        return locations

    def _find_feature_in_tests(self, feature_name: str, tests_dir: Path) -> list[str]:
        """Find feature in tests."""
        locations: list[str] = []

        if not tests_dir.exists():
            return locations

        # Check feature files
        for path in tests_dir.rglob("*.feature"):
            try:
                content = path.read_text(encoding="utf-8")
                if feature_name.lower() in content.lower():
                    for line_num, line in enumerate(content.splitlines(), 1):
                        if feature_name.lower() in line.lower():
                            locations.append(f"{path}:{line_num}")
            except (UnicodeDecodeError, OSError):
                continue

        # Check Python test files
        for path in tests_dir.rglob("*.py"):
            try:
                content = path.read_text(encoding="utf-8")
                if feature_name.lower() in content.lower():
                    for line_num, line in enumerate(content.splitlines(), 1):
                        if feature_name.lower() in line.lower():
                            locations.append(f"{path}:{line_num}")
            except (UnicodeDecodeError, OSError):
                continue

        return locations

    def _check_version_consistency(
        self,
        feature_name: str,
        docs_locations: list[str],
        code_locations: list[str],
        test_locations: list[str],
    ) -> list[str]:
        """Check version consistency across artifacts."""
        issues = []

        # Extract version information from different artifacts
        doc_versions = self._extract_versions_from_locations(docs_locations, "docs")
        code_versions = self._extract_versions_from_locations(code_locations, "code")
        test_versions = self._extract_versions_from_locations(test_locations, "tests")

        # Check for version mismatches
        all_versions = doc_versions + code_versions + test_versions

        if len(set(all_versions)) > 1:
            issues.append(f"Version inconsistency detected: {set(all_versions)}")

        return issues

    def _extract_versions_from_locations(
        self, locations: list[str], artifact_type: str
    ) -> list[str]:
        """Extract version information from artifact locations."""
        versions = []

        # Simple pattern matching for version info
        version_patterns = [
            r"v?(\d+\.\d+\.\d+)",
            r"version[:\s]*(\d+\.\d+)",
            r"Version[:\s]*(\d+\.\d+)",
        ]

        for location in locations:
            if ":" in location:
                file_path, line_num_str = location.split(":", 1)
                try:
                    line_num = int(line_num_str)
                    with open(file_path) as f:
                        lines = f.readlines()
                        if 0 <= line_num - 1 < len(lines):
                            line = lines[line_num - 1]
                            for pattern in version_patterns:
                                match = re.search(pattern, line, re.IGNORECASE)
                                if match:
                                    versions.append(match.group(1))
                except (ValueError, OSError):
                    continue

        return versions
