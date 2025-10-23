"""
Test Isolation Analyzer

This module analyzes test files for potential isolation issues and provides
recommendations for improving test isolation and determinism.

Key features:
- Detection of global state usage in tests
- Identification of shared resources between tests
- Analysis of fixture usage patterns
- Detection of potential state leakage between tests
- Recommendations for improving test isolation and determinism
"""

import ast
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field

from .enhanced_test_collector import IsolationIssue, IsolationReport


@dataclass
class GlobalStateIssue:
    """Represents a global state usage issue in tests."""
    variable_name: str
    file_path: str
    line_number: int
    issue_type: str
    description: str
    suggestion: str


@dataclass
class SharedResourceIssue:
    """Represents a shared resource issue in tests."""
    resource_type: str
    file_path: str
    line_number: int
    description: str
    suggestion: str


@dataclass
class FixtureAnalysis:
    """Analysis of fixture usage in a test file."""
    file_path: str
    fixtures_used: Set[str]
    fixtures_defined: Set[str]
    missing_fixtures: Set[str]
    unused_fixtures: Set[str]
    improper_fixture_usage: List[str]


@dataclass
class TestIsolationAnalysis:
    """Comprehensive analysis of test isolation issues."""
    global_state_issues: List[GlobalStateIssue]
    shared_resource_issues: List[SharedResourceIssue]
    fixture_analysis: FixtureAnalysis
    recommendations: List[str]
    overall_score: float


class TestIsolationAnalyzer:
    """
    Analyzes test files for potential isolation issues.

    This class examines test files for common isolation problems including:
    - Global state usage that could cause test interference
    - Shared resources that might not be properly cleaned up
    - Fixture usage patterns that could cause dependencies
    - Module-level state that could leak between tests
    """

    def __init__(self):
        """Initialize the test isolation analyzer."""
        # Patterns for detecting potential isolation issues
        self.global_state_patterns = [
            r"global\s+\w+",  # global variable declaration
            r"^(?!\s*(def|class|async def))(\w+)\s*=",  # module-level variable assignment
            r"os\.environ\[(.*?)\]\s*=",  # environment variable modification
            r"sys\.path\.append",  # sys.path modification
            r"open\([^)]+, ['\"][wa]['\"]",  # file writing without using tmpdir
        ]

        self.shared_resource_patterns = [
            r"\.connect\(",  # database connection
            r"\.open\(",  # file or connection opening
            r"requests\.",  # HTTP requests
            r"socket\.",  # socket operations
            r"subprocess\.",  # subprocess operations
        ]

        self.mocking_patterns = [
            r"mock\.",  # mock usage
            r"patch\(",  # patch usage
            r"MagicMock",  # MagicMock usage
            r"monkeypatch\.",  # monkeypatch usage
        ]

        self.fixture_patterns = [
            r"@pytest\.fixture",
            r"def \w+\(.*?request.*?\):",
            r"def \w+\(.*?tmpdir.*?\):",
            r"def \w+\(.*?tmp_path.*?\):"
        ]

    def analyze_test_isolation(self, directory: str) -> IsolationReport:
        """
        Analyze test isolation issues in a directory.

        Args:
            directory: Directory containing test files to analyze

        Returns:
            IsolationReport with analysis results
        """
        start_time = __import__("time").time()

        test_dir = Path(directory)
        if not test_dir.exists():
            return IsolationReport(
                total_issues=0,
                issues_by_severity={},
                issues_by_type={},
                issues=[],
                analysis_time=0.0,
                files_analyzed=0
            )

        all_issues = []
        files_analyzed = 0

        # Analyze each Python test file
        for py_file in test_dir.rglob("*.py"):
            if py_file.name.startswith("__") or not self._is_test_file(py_file):
                continue

            file_issues = self.analyze_test_file(str(py_file))
            all_issues.extend(file_issues)
            files_analyzed += 1

        # Categorize issues by severity and type
        issues_by_severity = {"high": 0, "medium": 0, "low": 0}
        issues_by_type = {}

        for issue in all_issues:
            issues_by_severity[issue.severity] += 1
            issues_by_type[issue.issue_type] = issues_by_type.get(issue.issue_type, 0) + 1

        analysis_time = __import__("time").time() - start_time

        return IsolationReport(
            total_issues=len(all_issues),
            issues_by_severity=issues_by_severity,
            issues_by_type=issues_by_type,
            issues=all_issues,
            analysis_time=analysis_time,
            files_analyzed=files_analyzed
        )

    def analyze_test_file(self, file_path: str) -> List[IsolationIssue]:
        """
        Analyze a specific test file for isolation issues.

        Args:
            file_path: Path to the test file to analyze

        Returns:
            List of isolation issues found
        """
        issues = []

        try:
            content = Path(file_path).read_text(encoding="utf-8")
            lines = content.splitlines()

            # Analyze global state usage
            issues.extend(self._analyze_global_state_usage(file_path, content, lines))

            # Analyze shared resource usage
            issues.extend(self._analyze_shared_resources(file_path, content, lines))

            # Analyze fixture usage
            issues.extend(self._analyze_fixture_usage(file_path, content, lines))

        except (UnicodeDecodeError, OSError) as e:
            issues.append(IsolationIssue(
                file_path=file_path,
                line_number=0,
                issue_type="file_error",
                severity="high",
                description=f"Could not read file: {e}",
                suggestion="Check file encoding and permissions"
            ))

        return issues

    def _analyze_global_state_usage(
        self,
        file_path: str,
        content: str,
        lines: List[str]
    ) -> List[IsolationIssue]:
        """Analyze global state usage in test file."""
        issues = []

        for line_num, line in enumerate(lines, 1):
            # Skip comments and docstrings
            if line.strip().startswith("#") or line.strip().startswith('"""') or line.strip().startswith("'''"):
                continue

            # Check for global state patterns
            for pattern in self.global_state_patterns:
                if re.search(pattern, line):
                    issues.append(IsolationIssue(
                        file_path=file_path,
                        line_number=line_num,
                        issue_type="global_state",
                        severity="medium",
                        description=f"Potential global state usage: {line.strip()}",
                        suggestion="Use fixtures or function parameters instead of global state"
                    ))

        return issues

    def _analyze_shared_resources(
        self,
        file_path: str,
        content: str,
        lines: List[str]
    ) -> List[IsolationIssue]:
        """Analyze shared resource usage in test file."""
        issues = []

        for line_num, line in enumerate(lines, 1):
            # Check for shared resource patterns
            for pattern in self.shared_resource_patterns:
                if re.search(pattern, line):
                    issues.append(IsolationIssue(
                        file_path=file_path,
                        line_number=line_num,
                        issue_type="shared_resource",
                        severity="low",
                        description=f"Potential shared resource usage: {line.strip()}",
                        suggestion="Consider using fixtures or mocking for external resources"
                    ))

        return issues

    def _analyze_fixture_usage(
        self,
        file_path: str,
        content: str,
        lines: List[str]
    ) -> List[IsolationIssue]:
        """Analyze fixture usage patterns in test file."""
        issues = []

        # Check if file uses pytest
        has_pytest_import = "import pytest" in content or "from pytest" in content

        if not has_pytest_import:
            return issues

        # Look for fixture usage patterns
        fixture_usage = set()
        fixture_definitions = set()

        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            # Check for fixture definitions
            if re.search(r"@pytest\.fixture", line) or re.search(r"def \w+.*fixture", line):
                # Extract fixture name from next non-empty line
                for next_line in lines[line_num:]:
                    next_line = next_line.strip()
                    if next_line.startswith("def "):
                        fixture_name = next_line.split("(")[0].replace("def ", "")
                        fixture_definitions.add(fixture_name)
                        break

            # Check for fixture usage in function parameters
            if line.startswith("def test_") or line.startswith("def ") and "test" in line:
                # Extract parameters
                if "(" in line:
                    params_str = line.split("(")[1].split(")")[0]
                    for param in params_str.split(","):
                        param = param.strip()
                        if param and not param.startswith("self"):
                            fixture_usage.add(param)

        # Check for missing or unused fixtures
        missing_fixtures = fixture_usage - fixture_definitions
        unused_fixtures = fixture_definitions - fixture_usage

        if missing_fixtures:
            for fixture in missing_fixtures:
                issues.append(IsolationIssue(
                    file_path=file_path,
                    line_number=0,  # Can't pinpoint exact line
                    issue_type="missing_fixture",
                    severity="high",
                    description=f"Using undefined fixture: {fixture}",
                    suggestion="Define the fixture or check for typos in fixture names"
                ))

        if unused_fixtures:
            for fixture in unused_fixtures:
                issues.append(IsolationIssue(
                    file_path=file_path,
                    line_number=0,  # Can't pinpoint exact line
                    issue_type="unused_fixture",
                    severity="low",
                    description=f"Unused fixture definition: {fixture}",
                    suggestion="Remove unused fixture or check if it's used elsewhere"
                ))

        return issues

    def _is_test_file(self, file_path: Path) -> bool:
        """Check if a file is a test file."""
        return (
            file_path.name.startswith("test_") or
            "test" in file_path.name or
            file_path.name.endswith("_test.py")
        )

    def generate_isolation_recommendations(
        self,
        report: IsolationReport
    ) -> List[str]:
        """
        Generate recommendations for improving test isolation.

        Args:
            report: Isolation report to generate recommendations for

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Analyze issues by type and provide targeted recommendations
        if report.issues_by_type.get("global_state", 0) > 0:
            recommendations.append(
                "Consider using pytest fixtures for shared test data instead of global variables"
            )
            recommendations.append(
                "Use temporary directories and files for file I/O operations in tests"
            )

        if report.issues_by_type.get("shared_resource", 0) > 0:
            recommendations.append(
                "Mock external dependencies (databases, APIs, file systems) to improve isolation"
            )
            recommendations.append(
                "Use pytest fixtures for resource setup and teardown"
            )

        if report.issues_by_type.get("missing_fixture", 0) > 0:
            recommendations.append(
                "Ensure all fixtures used in tests are properly defined"
            )
            recommendations.append(
                "Check for typos in fixture names and parameter names"
            )

        # General recommendations based on overall issues
        if report.total_issues > 10:
            recommendations.append(
                "Consider breaking large test files into smaller, more focused test modules"
            )

        if report.issues_by_severity.get("high", 0) > 0:
            recommendations.append(
                "Prioritize fixing high-severity isolation issues first"
            )

        # Add performance recommendations
        if report.analysis_time > 5.0:
            recommendations.append(
                "Consider using test file caching to improve analysis performance"
            )

        return recommendations

    def analyze_fixture_dependencies(self, test_file: str) -> Dict[str, Any]:
        """
        Analyze fixture dependencies in a test file.

        Args:
            test_file: Path to the test file to analyze

        Returns:
            Dictionary with fixture dependency analysis
        """
        try:
            content = Path(test_file).read_text(encoding="utf-8")
            tree = ast.parse(content)

            visitor = FixtureDependencyVisitor()
            visitor.visit(tree)

            return {
                "fixtures_used": visitor.fixtures_used,
                "fixtures_defined": visitor.fixtures_defined,
                "dependencies": visitor.dependencies,
                "circular_dependencies": visitor.circular_dependencies
            }

        except (UnicodeDecodeError, OSError, SyntaxError):
            return {
                "fixtures_used": set(),
                "fixtures_defined": set(),
                "dependencies": {},
                "circular_dependencies": []
            }


class FixtureDependencyVisitor(ast.NodeVisitor):
    """AST visitor that analyzes fixture dependencies in test files."""

    def __init__(self):
        self.fixtures_used = set()
        self.fixtures_defined = set()
        self.dependencies = {}
        self.current_function = None
        self.circular_dependencies = []

    def visit_FunctionDef(self, node):
        """Visit function definitions to find fixtures."""
        self.current_function = node.name

        # Check if this is a fixture definition
        for decorator in node.decorator_list:
            if self._is_fixture_decorator(decorator):
                self.fixtures_defined.add(node.name)

        # Check parameters for fixture usage
        for arg in node.args.args:
            if arg.arg not in ["self", "cls"]:
                self.fixtures_used.add(arg.arg)
                if self.current_function:
                    if self.current_function not in self.dependencies:
                        self.dependencies[self.current_function] = set()
                    self.dependencies[self.current_function].add(arg.arg)

        self.generic_visit(node)
        self.current_function = None

    def _is_fixture_decorator(self, decorator) -> bool:
        """Check if a decorator is a pytest fixture decorator."""
        if isinstance(decorator, ast.Name):
            return decorator.id == "fixture"
        elif isinstance(decorator, ast.Attribute):
            return (isinstance(decorator.value, ast.Name) and
                   decorator.value.id == "pytest" and
                   decorator.attr == "fixture")
        return False
