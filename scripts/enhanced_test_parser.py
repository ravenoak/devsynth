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
"""

import os
import sys
import ast
import re
import json
import inspect
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional, Union

# Constants
TEST_CATEGORIES = {
    "unit": "tests/unit",
    "integration": "tests/integration",
    "performance": "tests/performance",
    "property": "tests/property",
}

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
            if name.name == 'pytest':
                self.has_pytest_import = True
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        """Record imported modules."""
        if node.module:
            self.imported_modules.add(node.module)
            if node.module == 'pytest':
                self.has_pytest_import = True
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        """Visit class definitions to find test classes."""
        old_class = self.current_class
        self.current_class = node.name
        
        # Check if this is a test class (starts with 'Test')
        is_test_class = node.name.startswith('Test')
        
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
        is_test = node.name.startswith('test_')
        
        if is_test:
            # Extract markers from decorators
            markers = []
            for decorator in node.decorator_list:
                marker = self._extract_marker_from_decorator(decorator)
                if marker:
                    markers.append(marker)
            
            # If no specific markers found, use class-level markers
            if not markers and self.current_class and self.current_class in self.class_markers:
                markers = self.class_markers[self.current_class]
            
            # Determine the test path
            if self.current_class:
                test_path = f"{self.file_path}::{self.current_class}::{node.name}"
            else:
                test_path = f"{self.file_path}::{node.name}"
            
            # Check for parameterized tests
            is_parameterized = self._is_parameterized_test(node)
            
            # Add the test with its metadata
            self.tests.append({
                'path': test_path,
                'name': node.name,
                'class': self.current_class,
                'markers': markers,
                'is_parameterized': is_parameterized,
                'line_number': node.lineno
            })
            
            # If it's a parameterized test, try to extract the parameter values
            if is_parameterized:
                param_tests = self._extract_parameterized_tests(node, test_path)
                if param_tests:
                    self.tests.extend(param_tests)
        
        # Continue visiting the function body
        self.generic_visit(node)
    
    def _extract_marker_from_decorator(self, decorator: ast.expr) -> Optional[str]:
        """Extract marker type from a decorator node."""
        # Handle @pytest.mark.fast, @pytest.mark.medium, @pytest.mark.slow
        if isinstance(decorator, ast.Attribute) and isinstance(decorator.value, ast.Attribute):
            if (decorator.value.attr == 'mark' and 
                isinstance(decorator.value.value, ast.Name) and 
                decorator.value.value.id == 'pytest'):
                return decorator.attr
        
        # Handle @pytest.mark.fast(), @pytest.mark.medium(), @pytest.mark.slow()
        elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
            if (isinstance(decorator.func.value, ast.Attribute) and 
                decorator.func.value.attr == 'mark' and 
                isinstance(decorator.func.value.value, ast.Name) and 
                decorator.func.value.value.id == 'pytest'):
                return decorator.func.attr
        
        # Handle @mark.fast, @mark.medium, @mark.slow (when pytest.mark is imported as mark)
        elif isinstance(decorator, ast.Attribute) and isinstance(decorator.value, ast.Name):
            if decorator.value.id == 'mark' and 'pytest' in self.imported_modules:
                return decorator.attr
        
        # Handle @mark.fast(), @mark.medium(), @mark.slow()
        elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
            if (isinstance(decorator.func.value, ast.Name) and 
                decorator.func.value.id == 'mark' and 
                'pytest' in self.imported_modules):
                return decorator.func.attr
        
        return None
    
    def _is_parameterized_test(self, node: ast.FunctionDef) -> bool:
        """Check if a test function is parameterized."""
        # Look for @pytest.mark.parametrize or @parametrize decorators
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Attribute):
                    # @pytest.mark.parametrize
                    if (decorator.func.attr == 'parametrize' and 
                        isinstance(decorator.func.value, ast.Attribute) and 
                        decorator.func.value.attr == 'mark' and 
                        isinstance(decorator.func.value.value, ast.Name) and 
                        decorator.func.value.value.id == 'pytest'):
                        return True
                    # @mark.parametrize (when pytest.mark is imported as mark)
                    elif (decorator.func.attr == 'parametrize' and 
                          isinstance(decorator.func.value, ast.Name) and 
                          decorator.func.value.id == 'mark' and 
                          'pytest' in self.imported_modules):
                        return True
                elif isinstance(decorator.func, ast.Name):
                    # @parametrize (when pytest.mark.parametrize is imported as parametrize)
                    if decorator.func.id == 'parametrize' and 'pytest' in self.imported_modules:
                        return True
        
        return False
    
    def _extract_parameterized_tests(self, node: ast.FunctionDef, base_test_path: str) -> List[Dict[str, Any]]:
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
                if (decorator.func.attr == 'parametrize' and 
                    isinstance(decorator.func.value, ast.Attribute) and 
                    decorator.func.value.attr == 'mark' and 
                    isinstance(decorator.func.value.value, ast.Name) and 
                    decorator.func.value.value.id == 'pytest'):
                    is_parametrize = True
                # @mark.parametrize (when pytest.mark is imported as mark)
                elif (decorator.func.attr == 'parametrize' and 
                      isinstance(decorator.func.value, ast.Name) and 
                      decorator.func.value.id == 'mark' and 
                      'pytest' in self.imported_modules):
                    is_parametrize = True
            elif isinstance(decorator.func, ast.Name):
                # @parametrize (when pytest.mark.parametrize is imported as parametrize)
                if decorator.func.id == 'parametrize' and 'pytest' in self.imported_modules:
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
                    base_test = next((t for t in self.tests if t['path'] == base_test_path), None)
                    markers = base_test['markers'] if base_test else []
                    
                    # Create the parameterized test path
                    param_test_path = f"{base_test_path}[{param_value}]"
                    
                    # Add the parameterized test
                    param_tests.append({
                        'path': param_test_path,
                        'name': f"{node.name}[{param_value}]",
                        'class': self.current_class,
                        'markers': markers,
                        'is_parameterized': True,
                        'line_number': node.lineno,
                        'param_value': param_value
                    })
            
            except Exception as e:
                # If we can't extract parameter values, just continue
                print(f"Error extracting parameters from {base_test_path}: {e}")
                continue
        
        return param_tests
    
    def _get_param_value_str(self, node: ast.expr) -> Optional[str]:
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

def parse_test_file(file_path: str, use_cache: bool = True) -> List[Dict[str, Any]]:
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
        with open(file_path, 'r') as f:
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

def collect_tests_from_directory(directory: str, use_cache: bool = True) -> List[Dict[str, Any]]:
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
            if file.startswith('test_') and file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                # Parse the file to find tests
                file_tests = parse_test_file(file_path, use_cache)
                tests.extend(file_tests)
    
    return tests

def get_test_paths_from_directory(directory: str, use_cache: bool = True, include_file_only: bool = True) -> List[str]:
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
    test_paths = [test['path'] for test in tests]
    
    # If requested, also include file-only paths
    if include_file_only:
        # Get unique file paths
        file_paths = set()
        for test in tests:
            if '::' in test['path']:
                file_path = test['path'].split('::')[0]
                file_paths.add(file_path)
        
        # Add file-only paths to the result
        test_paths.extend(list(file_paths))
    
    return test_paths

def get_tests_with_markers(directory: str, marker_types: List[str] = ["fast", "medium", "slow"], 
                          use_cache: bool = True) -> Dict[str, List[str]]:
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
        for marker in test.get('markers', []):
            if marker in marker_types:
                tests_by_marker[marker].append(test['path'])
    
    return tests_by_marker

def get_marker_counts(directory: str, use_cache: bool = True) -> Dict[str, int]:
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

def compare_with_pytest(directory: str) -> Dict[str, Any]:
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
    cmd = [
        sys.executable, '-m', 'pytest',
        directory,
        '--collect-only',
        '-q'
    ]
    
    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        
        # Extract test paths from output
        pytest_tests = []
        for line in result.stdout.split('\n'):
            if line.strip() and not line.startswith('='):
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
            "only_in_parser": list(only_in_parser),
            "only_in_pytest": list(only_in_pytest),
            "discrepancy": abs(len(parser_tests) - len(pytest_tests))
        }
    
    except Exception as e:
        print(f"Error comparing with pytest: {e}")
        return {
            "error": str(e),
            "parser_count": len(parser_tests),
            "pytest_count": 0,
            "discrepancy": len(parser_tests)
        }

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Enhanced test parser for non-behavior tests."
    )
    parser.add_argument(
        "--directory",
        default="tests/unit",
        help="Directory to collect tests from"
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare with pytest collection"
    )
    parser.add_argument(
        "--markers",
        action="store_true",
        help="Show marker counts"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed information"
    )
    
    args = parser.parse_args()
    
    if args.compare:
        results = compare_with_pytest(args.directory)
        print(f"Comparison results for {args.directory}:")
        print(f"Parser count: {results['parser_count']}")
        print(f"Pytest count: {results['pytest_count']}")
        print(f"Common count: {results.get('common_count', 0)}")
        print(f"Only in parser: {results.get('only_in_parser_count', 0)}")
        print(f"Only in pytest: {results.get('only_in_pytest_count', 0)}")
        print(f"Discrepancy: {results['discrepancy']}")
        
        if args.verbose:
            if results.get('only_in_parser', []):
                print("\nTests only found by parser:")
                for test in sorted(results.get('only_in_parser', [])):
                    print(f"  {test}")
            
            if results.get('only_in_pytest', []):
                print("\nTests only found by pytest:")
                for test in sorted(results.get('only_in_pytest', [])):
                    print(f"  {test}")
    
    elif args.markers:
        marker_counts = get_marker_counts(args.directory)
        print(f"Marker counts for {args.directory}:")
        print(f"Fast: {marker_counts.get('fast', 0)}")
        print(f"Medium: {marker_counts.get('medium', 0)}")
        print(f"Slow: {marker_counts.get('slow', 0)}")
        
        # Get total test count
        tests = get_test_paths_from_directory(args.directory)
        print(f"Total tests: {len(tests)}")
        print(f"Tests with markers: {sum(marker_counts.values())}")
        print(f"Tests without markers: {len(tests) - sum(marker_counts.values())}")
    
    else:
        # Just collect and count tests
        tests = get_test_paths_from_directory(args.directory)
        print(f"Found {len(tests)} tests in {args.directory}")
        
        if args.verbose:
            for test in sorted(tests):
                print(f"  {test}")