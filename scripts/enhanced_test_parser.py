#!/usr/bin/env python3
"""
Enhanced Test Parser

This script provides a more accurate approach to parsing and detecting tests in Python files
using Abstract Syntax Tree (AST) analysis. It addresses the discrepancies in test counts
between pytest collection and file parsing for non-behavior tests.

Key features:
1. Robust detection of test functions and methods using AST
2. Support for parameterized tests with complex parameter expressions
3. Handling of nested classes and complex inheritance patterns
4. Accurate marker detection using AST-based decorator analysis
5. Support for various pytest test patterns and edge cases

Usage:
    from enhanced_test_parser import parse_test_file, collect_tests_from_directory

    # Parse a single test file
    tests = parse_test_file('tests/unit/test_example.py')

    # Collect all tests from a directory
    tests = collect_tests_from_directory('tests/unit')

    # Build a path for an integration test using templates
    path = build_test_path('integration', 'my_service', component='interface')
    print(path)
"""

import ast
import inspect
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Align marker detection with verify_test_markers.py
MARK_RE = re.compile(r"@pytest\.mark\.([a-zA-Z_][a-zA-Z0-9_]*)")

# Constants
TEST_CATEGORIES = {
    "unit": "tests/unit",
    "integration": "tests/integration",
    "performance": "tests/performance",
    "property": "tests/property",
}

# Templates for generating test file paths by category
TEST_TEMPLATES = {
    "unit": "tests/unit/test_{name}.py",
    "integration": "tests/integration/{component}/test_{name}.py",
    "performance": "tests/performance/test_{name}.py",
    "property": "tests/property/test_{name}.py",
}


def get_test_template(category: str) -> str:
    """Return the file path template for a test category.

    Args:
        category: Test category key such as "unit" or "integration".

    Returns:
        Path template string containing a ``{name}`` placeholder.

    Raises:
        KeyError: If the category is not defined in ``TEST_TEMPLATES``.
    """

    return TEST_TEMPLATES[category]


def build_test_path(category: str, name: str, **kwargs: str) -> str:
    """Build a test file path from a category and test name.

    Additional keyword arguments may be supplied for templates that
    require extra placeholders. For example, integration tests use a
    ``component`` placeholder to identify the target subsystem.

    Args:
        category: Test category such as ``"unit"`` or ``"integration"``.
        name: Base name of the test file without prefixes.
        **kwargs: Extra template parameters like ``component``.

    Returns:
        Fully formatted test file path.

    Raises:
        ValueError: If required template variables are missing.
    """

    template = get_test_template(category)
    try:
        return template.format(name=name, **kwargs)
    except KeyError as exc:  # pragma: no cover - direct KeyError capture
        missing = exc.args[0]
        raise ValueError(f"Missing template parameter: {missing}") from exc


# Cache for parsed files to improve performance
_file_cache = {}


class TestVisitor(ast.NodeVisitor):
    """AST visitor that finds test functions and methods with their markers."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.tests = []
        self.current_class = None
        self.class_markers = {}
        self.imported_modules = set()
        self.has_pytest_import = False

    def visit_Import(self, node):
        """Record imported modules."""
        for name in node.names:
            self.imported_modules.add(name.name)
            if name.name == "pytest":
                self.has_pytest_import = True
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """Record imported modules."""
        if node.module:
            self.imported_modules.add(node.module)
            if node.module == "pytest":
                self.has_pytest_import = True
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        """Visit class definitions to find test classes."""
        old_class = self.current_class
        self.current_class = node.name

        # Check if this is a test class (starts with 'Test')
        is_test_class = node.name.startswith("Test")

        # Extract class-level markers
        class_markers = []
        for decorator in node.decorator_list:
            marker = self._extract_marker_from_decorator(decorator)
            if marker:
                class_markers.append(marker)

        # Store class markers for use with methods
        if class_markers:
            self.class_markers[node.name] = class_markers

        # Visit class body
        self.generic_visit(node)

        # Restore previous class context
        self.current_class = old_class

    def visit_FunctionDef(self, node):
        """Visit function definitions to find test functions and methods."""
        # Check if this is a test function/method
        is_test = node.name.startswith("test_")

        if is_test:
            # Extract markers from decorators
            markers: list[str] = []
            for decorator in node.decorator_list:
                marker = self._extract_marker_from_decorator(decorator)
                if marker:
                    markers.append(marker)

            # If no specific markers found, use class-level markers
            if (
                not markers
                and self.current_class
                and self.current_class in self.class_markers
            ):
                markers = self.class_markers[self.current_class]

            # If still no markers, attempt to derive from @pytest.mark.parametrize pytest.param marks
            if not markers:
                param_speed = self._collect_parametrize_speed_markers_from_node(node)
                if param_speed:
                    markers = param_speed

            # Determine the test path
            if self.current_class:
                test_path = f"{self.file_path}::{self.current_class}::{node.name}"
            else:
                test_path = f"{self.file_path}::{node.name}"

            # Check for parameterized tests
            is_parameterized = self._is_parameterized_test(node)

            # Add the test with its metadata
            self.tests.append(
                {
                    "path": test_path,
                    "name": node.name,
                    "class": self.current_class,
                    "markers": markers,
                    "is_parameterized": is_parameterized,
                    "line_number": node.lineno,
                }
            )

            # If it's a parameterized test, try to extract the parameter values
            if is_parameterized:
                param_tests = self._extract_parameterized_tests(node, test_path)
                if param_tests:
                    self.tests.extend(param_tests)

        # Continue visiting the function body
        self.generic_visit(node)

    def _extract_marker_from_decorator(self, decorator: ast.expr) -> str | None:
        """Extract marker type from a decorator node."""
        # Handle @pytest.mark.fast, @pytest.mark.medium, @pytest.mark.slow
        if isinstance(decorator, ast.Attribute) and isinstance(
            decorator.value, ast.Attribute
        ):
            if (
                decorator.value.attr == "mark"
                and isinstance(decorator.value.value, ast.Name)
                and decorator.value.value.id == "pytest"
            ):
                return decorator.attr

        # Handle @pytest.mark.fast(), @pytest.mark.medium(), @pytest.mark.slow()
        elif isinstance(decorator, ast.Call) and isinstance(
            decorator.func, ast.Attribute
        ):
            if (
                isinstance(decorator.func.value, ast.Attribute)
                and decorator.func.value.attr == "mark"
                and isinstance(decorator.func.value.value, ast.Name)
                and decorator.func.value.value.id == "pytest"
            ):
                return decorator.func.attr

        # Handle @mark.fast, @mark.medium, @mark.slow (when pytest.mark is imported as mark)
        elif isinstance(decorator, ast.Attribute) and isinstance(
            decorator.value, ast.Name
        ):
            if decorator.value.id == "mark" and "pytest" in self.imported_modules:
                return decorator.attr

        # Handle @mark.fast(), @mark.medium(), @mark.slow()
        elif isinstance(decorator, ast.Call) and isinstance(
            decorator.func, ast.Attribute
        ):
            if (
                isinstance(decorator.func.value, ast.Name)
                and decorator.func.value.id == "mark"
                and "pytest" in self.imported_modules
            ):
                return decorator.func.attr

        return None

    def _is_parameterized_test(self, node: ast.FunctionDef) -> bool:
        """Check if a test function is parameterized."""
        # Look for @pytest.mark.parametrize or @parametrize decorators
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Attribute):
                    # @pytest.mark.parametrize
                    if (
                        decorator.func.attr == "parametrize"
                        and isinstance(decorator.func.value, ast.Attribute)
                        and decorator.func.value.attr == "mark"
                        and isinstance(decorator.func.value.value, ast.Name)
                        and decorator.func.value.value.id == "pytest"
                    ):
                        return True
                    # @mark.parametrize (when pytest.mark is imported as mark)
                    elif (
                        decorator.func.attr == "parametrize"
                        and isinstance(decorator.func.value, ast.Name)
                        and decorator.func.value.id == "mark"
                        and "pytest" in self.imported_modules
                    ):
                        return True
                elif isinstance(decorator.func, ast.Name):
                    # @parametrize (when pytest.mark.parametrize is imported as parametrize)
                    if (
                        decorator.func.id == "parametrize"
                        and "pytest" in self.imported_modules
                    ):
                        return True
        return False

    def _collect_parametrize_speed_markers_from_node(
        self, node: ast.FunctionDef
    ) -> list[str]:
        """Return a single speed marker from parametrize marks if all params agree.

        Mirrors behavior in scripts/verify_test_markers.py::_collect_parametrize_speed_markers.
        """
        speed_markers = {"fast", "medium", "slow"}
        # Scan decorators for @pytest.mark.parametrize
        for dec in node.decorator_list:
            if not (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)):
                continue
            if getattr(dec.func, "attr", None) != "parametrize":
                continue
            # Identify argvalues (2nd positional or argvalues= kw)
            argvalues = None
            if dec.args:
                argvalues = dec.args[1] if len(dec.args) >= 2 else None
            for kw in getattr(dec, "keywords", []) or []:
                if getattr(kw, "arg", None) == "argvalues":
                    argvalues = kw.value
                    break
            if argvalues is None:
                continue
            elements: list[ast.AST] = []
            if isinstance(argvalues, (ast.List, ast.Tuple)):
                elements = list(argvalues.elts)
            else:
                continue
            all_param_markers: list[str] = []
            for el in elements:
                if not isinstance(el, ast.Call):
                    all_param_markers = []
                    break
                # pytest.param(...) or from pytest import param
                is_param = False
                if isinstance(el.func, ast.Attribute):
                    is_param = (
                        getattr(el.func, "attr", "") == "param"
                        and isinstance(el.func.value, ast.Name)
                        and getattr(el.func.value, "id", "") == "pytest"
                    )
                elif isinstance(el.func, ast.Name):
                    is_param = el.func.id == "param"
                if not is_param:
                    all_param_markers = []
                    break
                # Find marks=...
                mark_value = None
                for kw in el.keywords or []:
                    if getattr(kw, "arg", None) == "marks":
                        mark_value = kw.value
                        break
                if mark_value is None:
                    all_param_markers = []
                    break
                # marks may be a single marker or list
                markers_here: list[str] = []
                if isinstance(mark_value, (ast.List, ast.Tuple)):
                    for v in mark_value.elts:
                        name = None
                        if isinstance(v, ast.Attribute):
                            name = getattr(v, "attr", None)
                        elif isinstance(v, ast.Call) and isinstance(
                            v.func, ast.Attribute
                        ):
                            name = getattr(v.func, "attr", None)
                        if isinstance(name, str) and name in speed_markers:
                            markers_here.append(name)
                else:
                    name = None
                    if isinstance(mark_value, ast.Attribute):
                        name = getattr(mark_value, "attr", None)
                    elif isinstance(mark_value, ast.Call) and isinstance(
                        mark_value.func, ast.Attribute
                    ):
                        name = getattr(mark_value.func, "attr", None)
                    if isinstance(name, str) and name in speed_markers:
                        markers_here.append(name)
                if len(markers_here) != 1:
                    all_param_markers = []
                    break
                all_param_markers.append(markers_here[0])
            if all_param_markers and len(set(all_param_markers)) == 1:
                return [all_param_markers[0]]
        return []

    def _extract_parameterized_tests(
        self, node: ast.FunctionDef, base_test_path: str
    ) -> list[dict[str, Any]]:
        """Extract individual test cases from a parameterized test."""
        param_tests = []

        # Look for @pytest.mark.parametrize or @parametrize decorators
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue

            # Check if this is a parametrize decorator
            is_parametrize = False
            if isinstance(decorator.func, ast.Attribute):
                # @pytest.mark.parametrize
                if (
                    decorator.func.attr == "parametrize"
                    and isinstance(decorator.func.value, ast.Attribute)
                    and decorator.func.value.attr == "mark"
                    and isinstance(decorator.func.value.value, ast.Name)
                    and decorator.func.value.value.id == "pytest"
                ):
                    is_parametrize = True
                # @mark.parametrize (when pytest.mark is imported as mark)
                elif (
                    decorator.func.attr == "parametrize"
                    and isinstance(decorator.func.value, ast.Name)
                    and decorator.func.value.id == "mark"
                    and "pytest" in self.imported_modules
                ):
                    is_parametrize = True
            elif isinstance(decorator.func, ast.Name):
                # @parametrize (when pytest.mark.parametrize is imported as parametrize)
                if (
                    decorator.func.id == "parametrize"
                    and "pytest" in self.imported_modules
                ):
                    is_parametrize = True

            if not is_parametrize or len(decorator.args) < 2:
                continue

            # Try to extract parameter values
            try:
                # Get parameter values from the second argument
                param_values = []

                # Handle list of tuples: [("value1", "value2"), ("value3", "value4")]
                if isinstance(decorator.args[1], ast.List):
                    for element in decorator.args[1].elts:
                        if isinstance(element, (ast.Tuple, ast.List)):
                            # For tuples/lists, use the first element as the parameter name
                            if element.elts:
                                param_value = self._get_param_value_str(element.elts[0])
                                if param_value:
                                    param_values.append(param_value)
                        else:
                            # For single values, use the value directly
                            param_value = self._get_param_value_str(element)
                            if param_value:
                                param_values.append(param_value)

                # Handle direct values: "value1", "value2"
                elif len(decorator.args) > 2:
                    for arg in decorator.args[1:]:
                        param_value = self._get_param_value_str(arg)
                        if param_value:
                            param_values.append(param_value)

                # Create a test entry for each parameter value
                for param_value in param_values:
                    # Extract markers from the base test
                    base_test = next(
                        (t for t in self.tests if t["path"] == base_test_path), None
                    )
                    markers = base_test["markers"] if base_test else []

                    # Create the parameterized test path
                    param_test_path = f"{base_test_path}[{param_value}]"

                    # Add the parameterized test
                    param_tests.append(
                        {
                            "path": param_test_path,
                            "name": f"{node.name}[{param_value}]",
                            "class": self.current_class,
                            "markers": markers,
                            "is_parameterized": True,
                            "line_number": node.lineno,
                            "param_value": param_value,
                        }
                    )

            except Exception as e:
                # If we can't extract parameter values, just continue
                print(f"Error extracting parameters from {base_test_path}: {e}")
                continue

        return param_tests

    def _get_param_value_str(self, node: ast.expr) -> str | None:
        """Convert an AST node to a string representation for parameter values."""
        if isinstance(node, ast.Constant):
            # For Python 3.8+
            return str(node.value)
        elif isinstance(node, ast.Str):
            # For older Python versions
            return node.s
        elif isinstance(node, ast.Num):
            # For older Python versions
            return str(node.n)
        elif isinstance(node, ast.Name):
            # For variable names
            return node.id
        elif isinstance(node, ast.Call):
            # For function calls, use the function name
            if isinstance(node.func, ast.Name):
                return f"{node.func.id}()"
            elif isinstance(node.func, ast.Attribute):
                return f"{node.func.attr}()"

        # For other types, return None
        return None


def parse_test_file(file_path: str, use_cache: bool = True) -> list[dict[str, Any]]:
    """
    Parse a test file to find test functions and methods using AST.

    Args:
        file_path: Path to the test file
        use_cache: Whether to use cached results

    Returns:
        List of test dictionaries with metadata
    """
    # Check cache first
    if use_cache and file_path in _file_cache:
        return _file_cache[file_path]

    # Check if the file exists
    if not os.path.exists(file_path):
        return []

    try:
        # Read the file content
        with open(file_path) as f:
            content = f.read()

        # Parse the file using AST
        tree = ast.parse(content, filename=file_path)

        # Visit the AST to find tests
        visitor = TestVisitor(file_path)
        visitor.visit(tree)

        # Cache the results
        if use_cache:
            _file_cache[file_path] = visitor.tests

        return visitor.tests

    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")
        return []
    except Exception as e:
        print(f"Error parsing file {file_path}: {e}")
        return []


def collect_tests_from_directory(
    directory: str, use_cache: bool = True
) -> list[dict[str, Any]]:
    """
    Collect tests from a directory by parsing Python files.

    Args:
        directory: Directory to collect tests from
        use_cache: Whether to use cached results

    Returns:
        List of test dictionaries with metadata
    """
    tests = []

    # Walk through the directory
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                file_path = os.path.join(root, file)

                # Parse the file to find tests
                file_tests = parse_test_file(file_path, use_cache)
                tests.extend(file_tests)

    return tests


def get_test_paths_from_directory(
    directory: str, use_cache: bool = True, include_file_only: bool = True
) -> list[str]:
    """
    Get test paths from a directory (compatible with common_test_collector format).

    Args:
        directory: Directory to collect tests from
        use_cache: Whether to use cached results
        include_file_only: Whether to include file-only paths (without function/method)

    Returns:
        List of test paths
    """
    tests = collect_tests_from_directory(directory, use_cache)

    # Get paths with function/method names
    test_paths = [test["path"] for test in tests]

    # If requested, also include file-only paths
    if include_file_only:
        # Get unique file paths
        file_paths = set()
        for test in tests:
            if "::" in test["path"]:
                file_path = test["path"].split("::")[0]
                file_paths.add(file_path)

        # Add file-only paths to the result
        test_paths.extend(list(file_paths))

    return test_paths


def get_tests_with_markers(
    directory: str,
    marker_types: list[str] = ["fast", "medium", "slow"],
    use_cache: bool = True,
) -> dict[str, list[str]]:
    """
    Get tests with specific markers from a directory.

    Args:
        directory: Directory to collect tests from
        marker_types: List of marker types to check for
        use_cache: Whether to use cached results

    Returns:
        Dictionary mapping marker types to lists of test paths
    """
    tests = collect_tests_from_directory(directory, use_cache)

    # Group tests by marker
    tests_by_marker = {marker: [] for marker in marker_types}

    for test in tests:
        for marker in test.get("markers", []):
            if marker in marker_types:
                tests_by_marker[marker].append(test["path"])

    return tests_by_marker


def get_marker_counts(directory: str, use_cache: bool = True) -> dict[str, int]:
    """
    Get counts of tests with specific markers from a directory.

    Args:
        directory: Directory to collect tests from
        use_cache: Whether to use cached results

    Returns:
        Dictionary mapping marker types to counts
    """
    tests_by_marker = get_tests_with_markers(directory, use_cache=use_cache)
    return {marker: len(tests) for marker, tests in tests_by_marker.items()}


def clear_cache():
    """Clear the file cache."""
    global _file_cache
    _file_cache = {}


def compare_with_pytest(directory: str) -> dict[str, Any]:
    """
    Compare test collection between this parser and pytest.

    Args:
        directory: Directory to collect tests from

    Returns:
        Dictionary with comparison results
    """
    import subprocess

    # Collect tests using this parser
    parser_tests = get_test_paths_from_directory(directory, use_cache=False)

    # Collect tests using pytest
    cmd = [sys.executable, "-m", "pytest", directory, "--collect-only", "-q"]

    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)

        # Extract test paths from output
        pytest_tests = []
        for line in result.stdout.split("\n"):
            if line.strip() and not line.startswith("="):
                pytest_tests.append(line.strip())

        # Compare results
        parser_set = set(parser_tests)
        pytest_set = set(pytest_tests)

        only_in_parser = parser_set - pytest_set
        only_in_pytest = pytest_set - parser_set
        common = parser_set.intersection(pytest_set)

        return {
            "parser_count": len(parser_tests),
            "pytest_count": len(pytest_tests),
            "common_count": len(common),
            "only_in_parser_count": len(only_in_parser),
            "only_in_pytest_count": len(only_in_pytest),
            "only_in_parser": list(sorted(only_in_parser)),
            "only_in_pytest": list(sorted(only_in_pytest)),
            "discrepancy": abs(len(parser_tests) - len(pytest_tests)),
        }

    except Exception as e:
        print(f"Error comparing with pytest: {e}")
        return {
            "error": str(e),
            "parser_count": len(parser_tests),
            "pytest_count": 0,
            "discrepancy": len(parser_tests),
        }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Enhanced test parser for non-behavior tests."
    )
    parser.add_argument(
        "--directory", default="tests/unit", help="Directory to collect tests from"
    )
    parser.add_argument(
        "--compare", action="store_true", help="Compare with pytest collection"
    )
    parser.add_argument("--markers", action="store_true", help="Show marker counts")
    parser.add_argument(
        "--report",
        action="store_true",
        help="Write a JSON summary report of marker counts (aligns with verify_test_markers)",
    )
    parser.add_argument(
        "--report-file",
        default="test_markers_report.json",
        help="Path to write JSON summary (default: test_markers_report.json)",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed information"
    )

    args = parser.parse_args()

    def _collect_marker_counts_text(dir_path: str) -> dict[str, int]:
        from collections import Counter

        counts: Counter[str] = Counter()
        for root, _, files in os.walk(dir_path):
            for file in files:
                if not file.endswith(".py"):
                    continue
                fp = os.path.join(root, file)
                try:
                    text = Path(fp).read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                for m in MARK_RE.finditer(text):
                    counts[m.group(1)] += 1
        return dict(counts)

    if args.compare:
        results = compare_with_pytest(args.directory)
        print(f"Comparison results for {args.directory}:")
        print(f"Parser count: {results['parser_count']}")
        print(f"Pytest count: {results['pytest_count']}")
        print(f"Common count: {results.get('common_count', 0)}")
        print(f"Only in parser: {results.get('only_in_parser_count', 0)}")
        print(f"Only in pytest: {results.get('only_in_pytest_count', 0)}")
        print(f"Discrepancy: {results['discrepancy']}")

        # Optionally write a JSON report of the comparison when --report is provided
        if args.report:
            out_path = Path(args.report_file)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
            print(f"Comparison report written to {out_path}")

        if args.verbose:
            if results.get("only_in_parser", []):
                print("\nTests only found by parser:")
                for test in sorted(results.get("only_in_parser", [])):
                    print(f"  {test}")

            if results.get("only_in_pytest", []):
                print("\nTests only found by pytest:")
                for test in sorted(results.get("only_in_pytest", [])):
                    print(f"  {test}")

    elif args.markers or args.report:
        # Use text-based regex to align with verify_test_markers for counts
        marker_counts = _collect_marker_counts_text(args.directory)
        print(f"Marker counts for {args.directory}:")
        for name in sorted(marker_counts.keys()):
            print(f"{name}: {marker_counts.get(name, 0)}")

        # Get total test count from parser
        tests = get_test_paths_from_directory(args.directory)
        print(f"Total tests (parser): {len(tests)}")

        if args.report:
            # Write JSON summary in the same shape as verify_test_markers
            summary = {
                "markers": marker_counts,
                "files_scanned": sum(1 for _ in Path(args.directory).rglob("*.py")),
                "files_with_issues": 0,  # parser does not perform import exec checks
            }
            out_path = Path(args.report_file)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
            print(f"Report written to {out_path}")

    else:
        # Just collect and count tests
        tests = get_test_paths_from_directory(args.directory)
        print(f"Found {len(tests)} tests in {args.directory}")

        if args.verbose:
            for test in sorted(tests):
                print(f"  {test}")
