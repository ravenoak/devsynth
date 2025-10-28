#!/usr/bin/env python3
"""
Test Isolation Analyzer

This script analyzes test files for potential isolation issues and provides
recommendations for improving test isolation and determinism. It helps address
the "test isolation and determinism" issues mentioned in docs/implementation/project_status.md.

Key features:
1. Detection of global state usage in tests
2. Identification of shared resources between tests
3. Analysis of fixture usage patterns
4. Detection of potential state leakage between tests
5. Recommendations for improving test isolation and determinism

Usage:
    from test_isolation_analyzer import analyze_test_isolation, analyze_test_file

    # Analyze all tests in a directory
    report = analyze_test_isolation("tests/unit")

    # Analyze a specific test file
    file_report = analyze_test_file("tests/unit/test_example.py")
"""

import ast
import inspect
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Import enhanced test parser for test collection
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    import enhanced_test_parser
except ImportError:
    print(
        "Warning: enhanced_test_parser.py not found, some functionality may be limited"
    )

# Constants
TEST_CATEGORIES = {
    "unit": "tests/unit",
    "integration": "tests/integration",
    "performance": "tests/performance",
    "property": "tests/property",
}

# Patterns for detecting potential isolation issues
GLOBAL_STATE_PATTERNS = [
    r"global\s+\w+",  # global variable declaration
    r"^(?!\s*(def|class))(\w+)\s*=",  # module-level variable assignment
    r"os\.environ\[(.*?)\]\s*=",  # environment variable modification
    r"sys\.path\.append",  # sys.path modification
    r"open\([^)]+, ['\"]w['\"]",  # file writing without using tmpdir
]

SHARED_RESOURCE_PATTERNS = [
    r"\.connect\(",  # database connection
    r"\.open\(",  # file or connection opening
    r"requests\.",  # HTTP requests
    r"socket\.",  # socket operations
    r"subprocess\.",  # subprocess operations
]

MOCKING_PATTERNS = [
    r"mock\.",  # mock usage
    r"patch\(",  # patch usage
    r"MagicMock",  # MagicMock usage
    r"monkeypatch\.",  # monkeypatch usage
]


class IsolationVisitor(ast.NodeVisitor):
    """AST visitor that finds potential isolation issues in tests."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.issues = []
        self.current_class = None
        self.current_function = None
        self.global_vars = set()
        self.fixture_uses = {}
        self.fixture_defs = {}
        self.mocks = set()
        self.has_setup_teardown = False
        self.imported_modules = set()

    def visit_Import(self, node):
        """Record imported modules."""
        for name in node.names:
            self.imported_modules.add(name.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """Record imported modules."""
        if node.module:
            self.imported_modules.add(node.module)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        """Visit class definitions to find test classes."""
        old_class = self.current_class
        self.current_class = node.name

        # Check if this is a test class (starts with 'Test')
        is_test_class = node.name.startswith("Test")

        if is_test_class:
            # Check for setup/teardown methods
            has_setup = any(
                child.name == "setUp" or child.name == "setup_method"
                for child in node.body
                if isinstance(child, ast.FunctionDef)
            )
            has_teardown = any(
                child.name == "tearDown" or child.name == "teardown_method"
                for child in node.body
                if isinstance(child, ast.FunctionDef)
            )

            if has_setup and has_teardown:
                self.has_setup_teardown = True
            elif has_setup and not has_teardown:
                self.issues.append(
                    {
                        "type": "missing_teardown",
                        "class": node.name,
                        "line": node.lineno,
                        "message": f"Class {node.name} has setUp but no tearDown method",
                    }
                )
            elif not has_setup and has_teardown:
                self.issues.append(
                    {
                        "type": "missing_setup",
                        "class": node.name,
                        "line": node.lineno,
                        "message": f"Class {node.name} has tearDown but no setUp method",
                    }
                )

        # Visit class body
        self.generic_visit(node)

        # Restore previous class context
        self.current_class = old_class

    def visit_FunctionDef(self, node):
        """Visit function definitions to find test functions and fixtures."""
        old_function = self.current_function
        self.current_function = node.name

        # Check if this is a test function/method
        is_test = node.name.startswith("test_")

        # Check if this is a fixture
        is_fixture = any(
            decorator.id == "fixture" if isinstance(decorator, ast.Name) else False
            for decorator in node.decorator_list
        )

        if is_fixture:
            # Record fixture definition
            fixture_name = node.name
            self.fixture_defs[fixture_name] = {
                "line": node.lineno,
                "has_yield": False,  # Will be updated if we find a yield
                "has_return": False,  # Will be updated if we find a return
                "has_teardown": False,  # Will be updated if we find code after yield
            }

            # Check fixture body for yield statements (for teardown)
            for child in ast.walk(node):
                if isinstance(child, ast.Yield):
                    self.fixture_defs[fixture_name]["has_yield"] = True
                    # Check if there's code after the yield (teardown)
                    yield_line = child.lineno
                    last_line = max(
                        stmt.lineno
                        for stmt in ast.walk(node)
                        if hasattr(stmt, "lineno")
                    )
                    if last_line > yield_line:
                        self.fixture_defs[fixture_name]["has_teardown"] = True
                elif isinstance(child, ast.Return):
                    self.fixture_defs[fixture_name]["has_return"] = True

        if is_test:
            # Check for fixture usage in test function arguments
            for arg in node.args.args:
                if arg.arg != "self":  # Skip 'self' in methods
                    self.fixture_uses.setdefault(arg.arg, []).append(node.name)

            # Check for potential isolation issues in the test function
            self._check_function_body(node)

        # Visit function body
        self.generic_visit(node)

        # Restore previous function context
        self.current_function = old_function

    def visit_Global(self, node):
        """Record global variable usage."""
        for name in node.names:
            self.global_vars.add(name)
            self.issues.append(
                {
                    "type": "global_state",
                    "name": name,
                    "function": self.current_function,
                    "class": self.current_class,
                    "line": node.lineno,
                    "message": f"Global variable '{name}' used in {'method' if self.current_class else 'function'} {self.current_function}",
                }
            )
        self.generic_visit(node)

    def visit_Assign(self, node):
        """Check for module-level assignments."""
        if not self.current_function and not self.current_class:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.global_vars.add(target.id)
        self.generic_visit(node)

    def visit_Call(self, node):
        """Check for calls to functions that might affect isolation."""
        # Check for mocking
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in ["patch", "mock", "MagicMock"]:
                self.mocks.add(f"{self.current_function or ''}")

        # Check for file operations without tmpdir
        if isinstance(node.func, ast.Name) and node.func.id == "open":
            if len(node.args) >= 2:
                # Check if the second argument indicates writing
                if isinstance(node.args[1], ast.Str) and (
                    "w" in node.args[1].s or "a" in node.args[1].s
                ):
                    # Check if tmpdir is not used
                    tmpdir_used = False
                    if (
                        isinstance(node.args[0], ast.Name)
                        and node.args[0].id == "tmpdir"
                    ):
                        tmpdir_used = True
                    elif (
                        isinstance(node.args[0], ast.Attribute)
                        and isinstance(node.args[0].value, ast.Name)
                        and node.args[0].value.id == "tmpdir"
                    ):
                        tmpdir_used = True

                    if not tmpdir_used:
                        self.issues.append(
                            {
                                "type": "file_operation",
                                "function": self.current_function,
                                "class": self.current_class,
                                "line": node.lineno,
                                "message": f"File writing operation without using tmpdir in {'method' if self.current_class else 'function'} {self.current_function}",
                            }
                        )

        self.generic_visit(node)

    def _check_function_body(self, node):
        """Check a function body for potential isolation issues."""
        # Convert the function body to source code
        source_lines = []
        for child in node.body:
            if hasattr(child, "lineno"):
                line_no = child.lineno
                col_offset = child.col_offset
                try:
                    with open(self.file_path) as f:
                        file_lines = f.readlines()
                        if line_no <= len(file_lines):
                            source_lines.append(file_lines[line_no - 1])
                except Exception:
                    pass

        source = "".join(source_lines)

        # Check for global state patterns
        for pattern in GLOBAL_STATE_PATTERNS:
            matches = re.finditer(pattern, source, re.MULTILINE)
            for match in matches:
                self.issues.append(
                    {
                        "type": "global_state",
                        "function": self.current_function,
                        "class": self.current_class,
                        "line": node.lineno + source[: match.start()].count("\n"),
                        "message": f"Potential global state usage in {'method' if self.current_class else 'function'} {self.current_function}: {match.group(0)}",
                    }
                )

        # Check for shared resource patterns
        for pattern in SHARED_RESOURCE_PATTERNS:
            matches = re.finditer(pattern, source, re.MULTILINE)
            for match in matches:
                self.issues.append(
                    {
                        "type": "shared_resource",
                        "function": self.current_function,
                        "class": self.current_class,
                        "line": node.lineno + source[: match.start()].count("\n"),
                        "message": f"Potential shared resource usage in {'method' if self.current_class else 'function'} {self.current_function}: {match.group(0)}",
                    }
                )


def analyze_test_file(file_path: str) -> dict[str, Any]:
    """
    Analyze a test file for potential isolation issues.

    Args:
        file_path: Path to the test file

    Returns:
        Dictionary with analysis results
    """
    # Check if the file exists
    if not os.path.exists(file_path):
        return {
            "file": file_path,
            "error": "File not found",
            "issues": [],
            "recommendations": [],
        }

    try:
        # Read the file content
        with open(file_path) as f:
            content = f.read()

        # Parse the file using AST
        tree = ast.parse(content, filename=file_path)

        # Visit the AST to find isolation issues
        visitor = IsolationVisitor(file_path)
        visitor.visit(tree)

        # Generate recommendations based on issues
        recommendations = generate_recommendations(visitor)

        return {
            "file": file_path,
            "issues": visitor.issues,
            "global_vars": list(visitor.global_vars),
            "fixture_uses": visitor.fixture_uses,
            "fixture_defs": visitor.fixture_defs,
            "has_setup_teardown": visitor.has_setup_teardown,
            "recommendations": recommendations,
        }

    except SyntaxError as e:
        return {
            "file": file_path,
            "error": f"Syntax error: {str(e)}",
            "issues": [],
            "recommendations": ["Fix syntax errors in the file"],
        }
    except Exception as e:
        return {
            "file": file_path,
            "error": f"Error analyzing file: {str(e)}",
            "issues": [],
            "recommendations": [],
        }


def generate_recommendations(visitor: IsolationVisitor) -> list[str]:
    """
    Generate recommendations based on isolation issues.

    Args:
        visitor: IsolationVisitor with analysis results

    Returns:
        List of recommendations
    """
    recommendations = []

    # Check for global state issues
    if visitor.global_vars:
        recommendations.append("Avoid using global variables in tests")
        recommendations.append("Use pytest fixtures for shared state")

    # Check for fixture usage
    if not visitor.fixture_uses:
        recommendations.append("Consider using pytest fixtures for setup and teardown")

    # Check for fixture definitions with missing teardown
    for fixture, info in visitor.fixture_defs.items():
        if info["has_yield"] and not info["has_teardown"]:
            recommendations.append(
                f"Add teardown code after yield in fixture '{fixture}'"
            )
        elif not info["has_yield"] and not info["has_return"]:
            recommendations.append(
                f"Consider adding a return or yield in fixture '{fixture}'"
            )

    # Check for setup/teardown
    if not visitor.has_setup_teardown and visitor.current_class:
        recommendations.append(
            "Consider adding setUp and tearDown methods to test classes"
        )

    # Check for mocking
    if visitor.mocks:
        recommendations.append("Ensure mocks are reset between tests")
        recommendations.append("Use monkeypatch fixture for patching")

    # Add general recommendations if there are issues
    if visitor.issues:
        recommendations.append("Use tmpdir fixture for file operations")
        recommendations.append("Isolate database operations")
        recommendations.append("Reset shared resources between tests")

    return recommendations


def analyze_test_isolation(directory: str = "tests") -> dict[str, Any]:
    """
    Analyze test isolation issues in a directory.

    Args:
        directory: Directory to analyze

    Returns:
        Dictionary with analysis results
    """
    # Initialize results
    results = {
        "total_files": 0,
        "files_with_issues": 0,
        "total_issues": 0,
        "issues_by_type": {},
        "files": [],
        "recommendations": set(),
    }

    # Find all test files
    test_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(os.path.join(root, file))

    results["total_files"] = len(test_files)

    # Analyze each file
    for file_path in test_files:
        file_results = analyze_test_file(file_path)

        # Count issues
        issues = file_results.get("issues", [])
        if issues:
            results["files_with_issues"] += 1
            results["total_issues"] += len(issues)

            # Count issues by type
            for issue in issues:
                issue_type = issue.get("type", "unknown")
                results["issues_by_type"][issue_type] = (
                    results["issues_by_type"].get(issue_type, 0) + 1
                )

        # Add file results
        results["files"].append(
            {
                "file": file_path,
                "issues_count": len(issues),
                "recommendations": file_results.get("recommendations", []),
            }
        )

        # Add recommendations to the overall set
        for recommendation in file_results.get("recommendations", []):
            results["recommendations"].add(recommendation)

    # Convert recommendations set to list
    results["recommendations"] = list(results["recommendations"])

    # Add general recommendations
    if results["total_issues"] > 0:
        results["recommendations"].extend(
            [
                "Use pytest fixtures for setup and teardown",
                "Avoid global state in tests",
                "Use monkeypatch for patching",
                "Reset mocks between tests",
                "Use tmpdir fixture for file operations",
                "Isolate database operations",
            ]
        )

    # Add specific recommendations based on issue types
    if results["issues_by_type"].get("global_state", 0) > 0:
        results["recommendations"].append(
            "Replace global variables with function-scoped fixtures"
        )

    if results["issues_by_type"].get("shared_resource", 0) > 0:
        results["recommendations"].append(
            "Use function-scoped fixtures for shared resources"
        )
        results["recommendations"].append("Consider using mocks for external resources")

    if results["issues_by_type"].get("file_operation", 0) > 0:
        results["recommendations"].append(
            "Always use tmpdir fixture for file operations"
        )

    # Remove duplicates from recommendations
    results["recommendations"] = list(set(results["recommendations"]))

    return results


def generate_isolation_best_practices() -> dict[str, list[str]]:
    """
    Generate best practices for test isolation and determinism.

    Returns:
        Dictionary with best practices by category
    """
    return {
        "fixtures": [
            "Use function-scoped fixtures for isolated tests",
            "Use module-scoped fixtures for expensive setup that can be shared",
            "Always clean up resources in fixtures (use yield for teardown)",
            "Use autouse=True sparingly, only for truly global setup/teardown",
            "Prefer explicit fixture dependencies over implicit ones",
        ],
        "mocking": [
            "Use monkeypatch fixture for patching",
            "Reset mocks between tests",
            "Avoid patching too deep in the call stack",
            "Be specific about what you're patching",
            "Verify that mocks are called as expected",
        ],
        "state_management": [
            "Avoid global variables in tests",
            "Don't rely on test execution order",
            "Reset shared state between tests",
            "Use tmpdir fixture for file operations",
            "Isolate database operations with transactions or separate databases",
        ],
        "test_design": [
            "Write small, focused tests",
            "Test one thing at a time",
            "Make tests independent of each other",
            "Avoid conditional logic in tests",
            "Use parameterized tests for testing multiple cases",
        ],
        "debugging": [
            "Use --showlocals for detailed failure information",
            "Use -v for verbose output",
            "Use --tb=native for Python-style tracebacks",
            "Use --collect-only to verify test collection",
            "Use -xvs to exit on first failure with verbose output and no capture",
        ],
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze test isolation issues.")
    parser.add_argument(
        "--directory", default="tests/unit", help="Directory to analyze"
    )
    parser.add_argument("--file", help="Specific file to analyze")
    parser.add_argument(
        "--best-practices",
        action="store_true",
        help="Generate best practices for test isolation",
    )
    parser.add_argument("--output", help="Output file for reports (JSON format)")
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed information"
    )

    args = parser.parse_args()

    if args.best_practices:
        best_practices = generate_isolation_best_practices()
        print("Best practices for test isolation and determinism:")

        for category, practices in best_practices.items():
            print(f"\n{category.upper()}:")
            for practice in practices:
                print(f"- {practice}")

        if args.output:
            with open(args.output, "w") as f:
                json.dump(best_practices, f, indent=2)

    elif args.file:
        results = analyze_test_file(args.file)
        print(f"Analysis results for {args.file}:")

        if "error" in results:
            print(f"Error: {results['error']}")
        else:
            print(f"Found {len(results['issues'])} potential isolation issues")

            if args.verbose:
                for issue in results["issues"]:
                    print(f"- {issue['message']} (line {issue['line']})")

            print("\nRecommendations:")
            for recommendation in results["recommendations"]:
                print(f"- {recommendation}")

        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)

    else:
        results = analyze_test_isolation(args.directory)
        print(f"Analysis results for {args.directory}:")
        print(f"Total files: {results['total_files']}")
        print(f"Files with issues: {results['files_with_issues']}")
        print(f"Total issues: {results['total_issues']}")

        if results["issues_by_type"]:
            print("\nIssues by type:")
            for issue_type, count in results["issues_by_type"].items():
                print(f"- {issue_type}: {count}")

        print("\nRecommendations:")
        for recommendation in results["recommendations"]:
            print(f"- {recommendation}")

        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)
