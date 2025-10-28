#!/usr/bin/env python3
"""
Test Dependency Analyzer Tool

This script analyzes all Python test files in the tests/ directory to detect:
- File system operations
- Network calls
- Global state modifications
- Tests marked with @pytest.mark.isolation

It generates JSON reports with dependency analysis and provides recommendations
for isolation marker removal.

Usage:
    python scripts/analyze_test_dependencies.py [--dry-run] [--apply] [--output FILE]

Examples:
    # Analyze and show recommendations
    python scripts/analyze_test_dependencies.py

    # Generate detailed report
    python scripts/analyze_test_dependencies.py --output analysis_report.json

    # Apply safe removals (dry run first)
    python scripts/analyze_test_dependencies.py --dry-run --apply
    python scripts/analyze_test_dependencies.py --apply
"""

import argparse
import ast
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pytest


class TestDependencyAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze test dependencies."""

    def __init__(self) -> None:
        self.file_operations: set[str] = set()
        self.network_calls: set[str] = set()
        self.global_state_modifications: set[str] = set()
        self.imports: set[str] = set()
        self.fixture_usage: set[str] = set()
        self.function_calls: set[str] = set()

        # Known patterns for different dependency types
        self.fs_patterns = {
            "open",
            "file",
            "Path",
            "pathlib",
            "os.path",
            "shutil",
            "tempfile",
            "glob",
            "makedirs",
            "rmdir",
            "remove",
            "rename",
            "copyfile",
            "tmp_path",
            "tmpdir",
            "tmpdir_factory",
            "temp_log_dir",
            "tmp_project_dir",
        }

        self.network_patterns = {
            "requests",
            "urllib",
            "http",
            "socket",
            "aiohttp",
            "httpx",
            "websocket",
            "ftp",
            "smtp",
            "telnet",
            "paramiko",
            "ssh",
        }

        self.global_state_patterns = {
            "os.environ",
            "sys.path",
            "sys.modules",
            "globals()",
            "locals()",
            "setattr",
            "delattr",
            "monkeypatch",
            "patch",
            "mock",
        }

    def visit_Import(self, node: ast.Import) -> None:
        """Track imports."""
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Track from imports."""
        if node.module:
            for alias in node.names:
                full_name = f"{node.module}.{alias.name}"
                self.imports.add(full_name)
                self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Track function calls."""
        call_name = self._get_call_name(node)
        if call_name:
            self.function_calls.add(call_name)

            # Categorize calls
            if any(pattern in call_name.lower() for pattern in self.fs_patterns):
                self.file_operations.add(call_name)
            if any(pattern in call_name.lower() for pattern in self.network_patterns):
                self.network_calls.add(call_name)
            if any(
                pattern in call_name.lower() for pattern in self.global_state_patterns
            ):
                self.global_state_modifications.add(call_name)

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Track test functions and their fixtures."""
        if node.name.startswith("test_"):
            # Extract fixture usage from function parameters
            for arg in node.args.args:
                if arg.arg in self.fs_patterns:
                    self.fixture_usage.add(arg.arg)
                    self.file_operations.add(f"fixture:{arg.arg}")
        self.generic_visit(node)

    def _get_call_name(self, node: ast.Call) -> str | None:
        """Extract the name of a function call."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return self._get_attribute_name(node.func)
        return None

    def _get_attribute_name(self, node: ast.Attribute) -> str:
        """Get full attribute name like 'os.path.join'."""
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        elif isinstance(node.value, ast.Attribute):
            return f"{self._get_attribute_name(node.value)}.{node.attr}"
        return node.attr


class TestFileAnalyzer:
    """Analyzes individual test files for dependencies."""

    def __init__(self) -> None:
        self.results: dict[str, Any] = {}

    def analyze_file(self, file_path: Path) -> dict[str, Any]:
        """Analyze a single test file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Parse AST
            tree = ast.parse(content, filename=str(file_path))

            # Analyze dependencies
            analyzer = TestDependencyAnalyzer()
            analyzer.visit(tree)

            # Check for isolation markers in source
            has_isolation_marker = "@pytest.mark.isolation" in content
            has_isolation_import = "pytest.mark.isolation" in content

            # Count test functions
            test_functions = [
                node.name
                for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
            ]

            try:
                relative_path = str(file_path.relative_to(Path.cwd()))
            except ValueError:
                relative_path = str(file_path)

            result = {
                "file_path": str(file_path),
                "relative_path": relative_path,
                "test_functions": test_functions,
                "test_count": len(test_functions),
                "has_isolation_marker": has_isolation_marker,
                "has_isolation_import": has_isolation_import,
                "dependencies": {
                    "file_operations": sorted(analyzer.file_operations),
                    "network_calls": sorted(analyzer.network_calls),
                    "global_state_modifications": sorted(
                        analyzer.global_state_modifications
                    ),
                    "imports": sorted(analyzer.imports),
                    "fixture_usage": sorted(analyzer.fixture_usage),
                    "function_calls": sorted(analyzer.function_calls),
                },
                "risk_score": self._calculate_risk_score(analyzer),
                "safe_for_parallel": self._is_safe_for_parallel(
                    analyzer, has_isolation_marker
                ),
            }

            return result

        except Exception as e:
            return {"file_path": str(file_path), "error": str(e), "analyzable": False}

    def _calculate_risk_score(self, analyzer: TestDependencyAnalyzer) -> int:
        """Calculate risk score for removing isolation marker."""
        score = 0
        score += len(analyzer.file_operations) * 3
        score += len(analyzer.network_calls) * 5
        score += len(analyzer.global_state_modifications) * 4
        return score

    def _is_safe_for_parallel(
        self, analyzer: TestDependencyAnalyzer, has_marker: bool
    ) -> bool:
        """Determine if test is safe for parallel execution."""
        if not has_marker:
            return True  # Already parallel-safe

        # Consider safe if no risky dependencies
        return (
            len(analyzer.file_operations) == 0
            and len(analyzer.network_calls) == 0
            and len(analyzer.global_state_modifications) <= 1  # Allow minimal mocking
        )


def find_test_files(test_dir: Path) -> list[Path]:
    """Find all test files in the test directory."""
    test_files = []
    for pattern in ["test_*.py", "*_test.py"]:
        test_files.extend(test_dir.rglob(pattern))
    return sorted(test_files)


def load_existing_analysis(output_file: Path) -> dict[str, Any]:
    """Load existing analysis if available."""
    if output_file.exists():
        try:
            with open(output_file) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def generate_recommendations(analysis_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate recommendations based on analysis results."""
    total_files = len(analysis_results)
    files_with_isolation = sum(
        1 for r in analysis_results if r.get("has_isolation_marker", False)
    )
    safe_for_removal = sum(
        1
        for r in analysis_results
        if r.get("safe_for_parallel", False) and r.get("has_isolation_marker", False)
    )

    # Categorize by risk level
    low_risk = [
        r
        for r in analysis_results
        if r.get("risk_score", 0) <= 2 and r.get("has_isolation_marker", False)
    ]
    medium_risk = [
        r
        for r in analysis_results
        if 3 <= r.get("risk_score", 0) <= 8 and r.get("has_isolation_marker", False)
    ]
    high_risk = [
        r
        for r in analysis_results
        if r.get("risk_score", 0) > 8 and r.get("has_isolation_marker", False)
    ]

    return {
        "summary": {
            "total_test_files": total_files,
            "files_with_isolation_markers": files_with_isolation,
            "safe_for_removal": safe_for_removal,
            "removal_percentage": round(
                (
                    (safe_for_removal / files_with_isolation * 100)
                    if files_with_isolation > 0
                    else 0
                ),
                1,
            ),
        },
        "risk_categories": {
            "low_risk": {
                "count": len(low_risk),
                "files": [r["relative_path"] for r in low_risk],
            },
            "medium_risk": {
                "count": len(medium_risk),
                "files": [r["relative_path"] for r in medium_risk],
            },
            "high_risk": {
                "count": len(high_risk),
                "files": [r["relative_path"] for r in high_risk],
            },
        },
        "recommendations": {
            "immediate_removal": [r["relative_path"] for r in low_risk],
            "careful_review": [r["relative_path"] for r in medium_risk],
            "keep_isolation": [r["relative_path"] for r in high_risk],
        },
    }


def apply_recommendations(
    recommendations: dict[str, Any], dry_run: bool = True
) -> dict[str, Any]:
    """Apply isolation marker removal recommendations."""
    if dry_run:
        print("DRY RUN: Would remove isolation markers from the following files:")
        for file_path in recommendations["recommendations"]["immediate_removal"]:
            print(f"  - {file_path}")
        return {"dry_run": True, "files_modified": 0}

    modified_files = []
    for file_path in recommendations["recommendations"]["immediate_removal"]:
        try:
            full_path = Path(file_path)
            if not full_path.exists():
                continue

            with open(full_path, encoding="utf-8") as f:
                content = f.read()

            # Remove isolation markers
            lines = content.split("\n")
            new_lines = []
            skip_next = False

            for i, line in enumerate(lines):
                if skip_next:
                    skip_next = False
                    continue

                if "@pytest.mark.isolation" in line:
                    # Skip this line and potentially the next if it's just whitespace
                    if i + 1 < len(lines) and lines[i + 1].strip() == "":
                        skip_next = True
                    continue

                new_lines.append(line)

            # Write back if changed
            new_content = "\n".join(new_lines)
            if new_content != content:
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                modified_files.append(str(file_path))

        except Exception as e:
            print(f"Error modifying {file_path}: {e}")

    return {
        "dry_run": False,
        "files_modified": len(modified_files),
        "modified_files": modified_files,
    }


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze test dependencies and isolation marker usage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("test_reports/test_dependency_analysis.json"),
        help="Output file for analysis report (default: test_reports/test_dependency_analysis.json)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes",
    )

    parser.add_argument(
        "--apply", action="store_true", help="Apply safe isolation marker removals"
    )

    parser.add_argument(
        "--test-dir",
        type=Path,
        default=Path("tests"),
        help="Test directory to analyze (default: tests)",
    )

    args = parser.parse_args()

    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Find test files
    if not args.test_dir.exists():
        print(f"Error: Test directory {args.test_dir} does not exist")
        return 1

    test_files = find_test_files(args.test_dir)
    if not test_files:
        print(f"No test files found in {args.test_dir}")
        return 1

    print(f"Analyzing {len(test_files)} test files...")

    # Analyze files
    analyzer = TestFileAnalyzer()
    results = []

    for test_file in test_files:
        try:
            rel_path = test_file.relative_to(Path.cwd())
        except ValueError:
            rel_path = test_file
        print(f"  Analyzing {rel_path}...")
        result = analyzer.analyze_file(test_file)
        results.append(result)

    # Generate recommendations
    recommendations = generate_recommendations(results)

    # Create full report
    report = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "tool_version": "1.0.0",
            "test_directory": str(args.test_dir),
            "total_files_analyzed": len(results),
        },
        "analysis_results": results,
        "recommendations": recommendations,
    }

    # Save report
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2, sort_keys=True)

    # Print summary
    print(f"\nAnalysis complete. Report saved to {args.output}")
    print(f"Summary:")
    print(f"  Total test files: {recommendations['summary']['total_test_files']}")
    print(
        f"  Files with isolation markers: {recommendations['summary']['files_with_isolation_markers']}"
    )
    print(
        f"  Safe for removal: {recommendations['summary']['safe_for_removal']} ({recommendations['summary']['removal_percentage']}%)"
    )

    print(f"\nRisk breakdown:")
    print(
        f"  Low risk (immediate removal): {recommendations['risk_categories']['low_risk']['count']}"
    )
    print(
        f"  Medium risk (careful review): {recommendations['risk_categories']['medium_risk']['count']}"
    )
    print(
        f"  High risk (keep isolation): {recommendations['risk_categories']['high_risk']['count']}"
    )

    # Apply changes if requested
    if args.apply:
        print(f"\nApplying recommendations...")
        application_result = apply_recommendations(
            recommendations, dry_run=args.dry_run
        )

        if args.dry_run:
            print("Dry run completed. Use --apply without --dry-run to make changes.")
        else:
            print(f"Modified {application_result['files_modified']} files")
            if application_result["modified_files"]:
                print("Modified files:")
                for file_path in application_result["modified_files"]:
                    print(f"  - {file_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
