#!/usr/bin/env python3
"""
Safe Isolation Marker Removal Tool

This script implements safe removal of isolation markers based on careful analysis
of test dependencies and patterns. It focuses on tests that use proper pytest
fixtures and patterns that are designed for parallel execution.

Usage:
    python scripts/safe_isolation_removal.py [--dry-run] [--target FILE] [--batch-size N]

Examples:
    # Analyze specific file
    python scripts/safe_isolation_removal.py --target tests/unit/application/cli/commands/test_run_tests_cmd_more.py --dry-run

    # Remove markers from medium-risk files
    python scripts/safe_isolation_removal.py --dry-run
    python scripts/safe_isolation_removal.py
"""

import argparse
import ast
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

import pytest


class SafeRemovalAnalyzer:
    """Enhanced analyzer for safe isolation marker removal."""

    def __init__(self) -> None:
        # Patterns that are safe for parallel execution when properly used
        self.safe_patterns = {
            "monkeypatch",  # pytest's monkeypatch is thread-safe
            "mock",  # unittest.mock is generally safe
            "patch",  # unittest.mock.patch with proper context
            "tmp_path",  # pytest's tmp_path is isolated per test
            "tmpdir",  # pytest's tmpdir is isolated per test
            "caplog",  # pytest's caplog is thread-safe
            "capsys",  # pytest's capsys is thread-safe
        }

        # Patterns that indicate real resource conflicts
        self.unsafe_patterns = {
            "os.chdir",  # Changes global working directory
            "os.environ",  # Direct environment modification (without monkeypatch)
            "sys.path",  # Direct sys.path modification
            "socket.bind",  # Network resource binding
            "threading",  # Direct threading without proper isolation
            "multiprocessing",  # Process-level operations
        }

    def analyze_test_safety(self, file_path: Path) -> dict[str, Any]:
        """Analyze if a test file is safe for parallel execution."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))

            # Check for isolation marker
            has_isolation_marker = "@pytest.mark.isolation" in content
            if not has_isolation_marker:
                return {
                    "safe_for_removal": False,
                    "reason": "No isolation marker found",
                }

            # Analyze AST for patterns
            safe_score = 0
            unsafe_score = 0
            patterns_found = set()

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    call_name = self._get_call_name(node)
                    if call_name:
                        patterns_found.add(call_name)

                        # Check safe patterns
                        if any(
                            safe_pattern in call_name.lower()
                            for safe_pattern in self.safe_patterns
                        ):
                            safe_score += 1

                        # Check unsafe patterns
                        if any(
                            unsafe_pattern in call_name.lower()
                            for unsafe_pattern in self.unsafe_patterns
                        ):
                            unsafe_score += 3

            # Check for proper fixture usage
            uses_proper_fixtures = any(
                pattern in content
                for pattern in [
                    "monkeypatch:",
                    "monkeypatch.",
                    "tmp_path:",
                    "tmp_path.",
                    "caplog:",
                    "caplog.",
                ]
            )

            # Check for direct global modifications
            has_direct_global_mods = any(
                pattern in content
                for pattern in [
                    "os.environ[",
                    "sys.path.",
                    "globals()[",
                    "os.chdir(",
                    "setattr(sys,",
                ]
            )

            # Decision logic
            if unsafe_score > 0:
                return {
                    "safe_for_removal": False,
                    "reason": f"Unsafe patterns detected (score: {unsafe_score})",
                    "unsafe_patterns": [
                        p
                        for p in patterns_found
                        if any(up in p.lower() for up in self.unsafe_patterns)
                    ],
                }

            if uses_proper_fixtures and not has_direct_global_mods:
                return {
                    "safe_for_removal": True,
                    "reason": "Uses proper pytest fixtures without direct global modifications",
                    "safe_patterns": [
                        p
                        for p in patterns_found
                        if any(sp in p.lower() for sp in self.safe_patterns)
                    ],
                }

            if safe_score >= 3 and unsafe_score == 0:
                return {
                    "safe_for_removal": True,
                    "reason": f"High safe pattern usage (score: {safe_score}) with no unsafe patterns",
                }

            return {
                "safe_for_removal": False,
                "reason": f"Insufficient confidence (safe: {safe_score}, unsafe: {unsafe_score})",
                "patterns_found": sorted(patterns_found),
            }

        except Exception as e:
            return {
                "safe_for_removal": False,
                "reason": f"Analysis error: {str(e)}",
                "error": True,
            }

    def _get_call_name(self, node: ast.Call) -> str:
        """Extract the name of a function call."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return self._get_attribute_name(node.func)
        return ""

    def _get_attribute_name(self, node: ast.Attribute) -> str:
        """Get full attribute name like 'os.path.join'."""
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        elif isinstance(node.value, ast.Attribute):
            return f"{self._get_attribute_name(node.value)}.{node.attr}"
        return node.attr


def remove_isolation_marker(file_path: Path, dry_run: bool = True) -> dict[str, Any]:
    """Remove isolation marker from a file."""
    if dry_run:
        return {"dry_run": True, "would_modify": str(file_path)}

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")
        new_lines = []
        skip_next = False
        modified = False

        for i, line in enumerate(lines):
            if skip_next:
                skip_next = False
                continue

            if "@pytest.mark.isolation" in line:
                modified = True
                # Skip this line and potentially the next if it's just whitespace
                if i + 1 < len(lines) and lines[i + 1].strip() == "":
                    skip_next = True
                continue

            new_lines.append(line)

        if modified:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(new_lines))

            return {"modified": True, "file_path": str(file_path)}
        else:
            return {"modified": False, "reason": "No isolation marker found"}

    except Exception as e:
        return {"error": str(e), "file_path": str(file_path)}


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Safely remove isolation markers from tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument("--target", type=Path, help="Specific file to analyze/modify")

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Maximum number of files to modify in one run (default: 5)",
    )

    parser.add_argument(
        "--analysis-file",
        type=Path,
        default=Path("test_reports/test_dependency_analysis.json"),
        help="Dependency analysis file to use",
    )

    args = parser.parse_args()

    analyzer = SafeRemovalAnalyzer()

    if args.target:
        # Analyze specific file
        print(f"Analyzing {args.target}...")
        result = analyzer.analyze_test_safety(args.target)

        print(f"Safe for removal: {result['safe_for_removal']}")
        print(f"Reason: {result['reason']}")

        if result.get("safe_patterns"):
            print(f"Safe patterns: {result['safe_patterns']}")
        if result.get("unsafe_patterns"):
            print(f"Unsafe patterns: {result['unsafe_patterns']}")

        if result["safe_for_removal"]:
            print(f"\nRemoving isolation marker...")
            removal_result = remove_isolation_marker(args.target, dry_run=args.dry_run)
            if removal_result.get("modified"):
                print(f"✓ Modified {args.target}")
            elif removal_result.get("would_modify"):
                print(f"✓ Would modify {args.target} (dry run)")
            else:
                print(f"No changes needed: {removal_result.get('reason', 'Unknown')}")

        return 0

    # Load dependency analysis
    if not args.analysis_file.exists():
        print(f"Error: Analysis file {args.analysis_file} not found")
        print("Run: python scripts/analyze_test_dependencies.py first")
        return 1

    with open(args.analysis_file) as f:
        analysis_data = json.load(f)

    # Get medium-risk files for careful review
    medium_risk_files = (
        analysis_data.get("recommendations", {})
        .get("risk_categories", {})
        .get("medium_risk", {})
        .get("files", [])
    )

    if not medium_risk_files:
        print("No medium-risk files found for review")
        return 0

    print(f"Found {len(medium_risk_files)} medium-risk files for careful review:")

    modifications = []
    for file_path in medium_risk_files[: args.batch_size]:
        print(f"\nAnalyzing {file_path}...")
        full_path = Path(file_path)

        if not full_path.exists():
            print(f"  File not found: {file_path}")
            continue

        result = analyzer.analyze_test_safety(full_path)
        print(f"  Safe for removal: {result['safe_for_removal']}")
        print(f"  Reason: {result['reason']}")

        if result["safe_for_removal"]:
            removal_result = remove_isolation_marker(full_path, dry_run=args.dry_run)
            modifications.append(
                {"file": file_path, "result": removal_result, "analysis": result}
            )

            if args.dry_run:
                print(f"  ✓ Would remove isolation marker (dry run)")
            else:
                print(f"  ✓ Removed isolation marker")
        else:
            print(f"  ✗ Keeping isolation marker")

    # Summary
    if modifications:
        print(f"\nSummary:")
        print(f"  Files analyzed: {len(medium_risk_files[:args.batch_size])}")
        print(f"  Modifications: {len(modifications)}")

        if args.dry_run:
            print("  This was a dry run. Use without --dry-run to apply changes.")
        else:
            print("  Changes applied successfully.")
            print("\nNext steps:")
            print("  1. Run the test suite to verify parallel execution works")
            print("  2. Measure performance improvement")
            print("  3. If issues occur, restore markers with git checkout")

    return 0


if __name__ == "__main__":
    sys.exit(main())
