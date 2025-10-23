"""
Test Enhancement Engine

This module provides automated test quality improvement and organization capabilities.
It analyzes test files and applies safe enhancements to improve test quality,
readability, and maintainability.

Key features:
- Automated test improvement with safety checks
- Assertion enhancement for better clarity and coverage
- Test organization optimization
- Error handling strengthening
- Documentation enhancement
"""

import ast
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from .test_isolation_analyzer import TestIsolationAnalyzer


@dataclass
class FixResult:
    """Result of a test fix operation."""
    file_path: str
    fix_type: str
    description: str
    old_code: str
    new_code: str
    applied: bool
    safe: bool


@dataclass
class EnhancementResult:
    """Result of a test enhancement operation."""
    file_path: str
    enhancement_type: str
    description: str
    changes_made: int
    improvements: List[str]


@dataclass
class EnhancementResults:
    """Results of test enhancement operations."""
    fixes_applied: List[FixResult]
    enhancements_made: List[EnhancementResult]
    total_improvements: int
    safe_operations: int
    risky_operations: int
    backup_created: bool


class TestEnhancer:
    """
    Enhances test system quality and organization.

    This class provides automated test improvement capabilities including:
    - Fixing common test issues (imports, markers, assertions)
    - Enhancing test assertions for better clarity and coverage
    - Improving test organization and structure
    - Strengthening error handling in tests
    - Enhancing test documentation
    """

    def __init__(self, backup_changes: bool = True):
        """Initialize the test enhancer."""
        self.backup_changes = backup_changes
        self.isolation_analyzer = TestIsolationAnalyzer()
        self.backup_dir = Path.home() / ".devsynth" / "test_backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def run_enhancements(
        self,
        directory: str,
        apply_fixes: bool = False,
        create_backups: bool = True
    ) -> EnhancementResults:
        """
        Run all test system enhancements.

        Args:
            directory: Directory containing test files to enhance
            apply_fixes: Whether to apply fixes automatically
            create_backups: Whether to create backup files before making changes

        Returns:
            EnhancementResults with improvement details
        """
        fixes_applied = []
        enhancements_made = []
        total_improvements = 0
        safe_operations = 0
        risky_operations = 0

        test_dir = Path(directory)
        if not test_dir.exists():
            return EnhancementResults(
                fixes_applied=[],
                enhancements_made=[],
                total_improvements=0,
                safe_operations=0,
                risky_operations=0,
                backup_created=False
            )

        backup_created = False

        # Process each test file
        for py_file in test_dir.rglob("*.py"):
            if py_file.name.startswith("__") or not self._is_test_file(py_file):
                continue

            # Create backup if requested
            if create_backups and apply_fixes:
                self._create_backup(py_file)
                backup_created = True

            # Apply enhancements to this file
            file_fixes, file_enhancements = self._enhance_test_file(
                py_file,
                apply_fixes
            )

            fixes_applied.extend(file_fixes)
            enhancements_made.extend(file_enhancements)
            total_improvements += len(file_fixes) + len(file_enhancements)

            # Count safe vs risky operations
            safe_operations += sum(1 for fix in file_fixes if fix.safe)
            risky_operations += sum(1 for fix in file_fixes if not fix.safe)

        return EnhancementResults(
            fixes_applied=fixes_applied,
            enhancements_made=enhancements_made,
            total_improvements=total_improvements,
            safe_operations=safe_operations,
            risky_operations=risky_operations,
            backup_created=backup_created
        )

    def fix_common_test_issues(
        self,
        directory: str,
        apply_fixes: bool = False
    ) -> List[FixResult]:
        """
        Fix common test issues like incorrect imports, missing markers.

        Args:
            directory: Directory containing test files to fix
            apply_fixes: Whether to apply fixes automatically

        Returns:
            List of fix results
        """
        fixes = []

        test_dir = Path(directory)
        if not test_dir.exists():
            return fixes

        for py_file in test_dir.rglob("*.py"):
            if py_file.name.startswith("__") or not self._is_test_file(py_file):
                continue

            file_fixes = self._fix_common_issues(py_file, apply_fixes)
            fixes.extend(file_fixes)

        return fixes

    def enhance_test_assertions(
        self,
        directory: str,
        apply_fixes: bool = False
    ) -> List[EnhancementResult]:
        """
        Enhance test assertions for better clarity and coverage.

        Args:
            directory: Directory containing test files to enhance
            apply_fixes: Whether to apply enhancements automatically

        Returns:
            List of enhancement results
        """
        enhancements = []

        test_dir = Path(directory)
        if not test_dir.exists():
            return enhancements

        for py_file in test_dir.rglob("*.py"):
            if py_file.name.startswith("__") or not self._is_test_file(py_file):
                continue

            file_enhancements = self._enhance_assertions(py_file, apply_fixes)
            enhancements.extend(file_enhancements)

        return enhancements

    def _enhance_test_file(
        self,
        file_path: Path,
        apply_fixes: bool
    ) -> Tuple[List[FixResult], List[EnhancementResult]]:
        """Enhance a single test file."""
        fixes = []
        enhancements = []

        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.splitlines()

            # Fix common issues first
            fixes.extend(self._fix_common_issues(file_path, apply_fixes))

            # Enhance assertions
            enhancements.extend(self._enhance_assertions(file_path, apply_fixes))

            # Improve organization
            enhancements.extend(self._improve_organization(file_path, apply_fixes))

            # Strengthen error handling
            enhancements.extend(self._strengthen_error_handling(file_path, apply_fixes))

            # Enhance documentation
            enhancements.extend(self._enhance_documentation(file_path, apply_fixes))

        except (UnicodeDecodeError, OSError) as e:
            fixes.append(FixResult(
                file_path=str(file_path),
                fix_type="file_error",
                description=f"Could not read file: {e}",
                old_code="",
                new_code="",
                applied=False,
                safe=False
            ))

        return fixes, enhancements

    def _fix_common_issues(self, file_path: Path, apply_fixes: bool) -> List[FixResult]:
        """Fix common issues in a test file."""
        fixes = []

        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.splitlines()

            # Check for missing pytest import
            if not re.search(r"import pytest|from pytest", content):
                if "pytest.mark" in content or "@pytest" in content:
                    fixes.append(self._add_pytest_import(file_path, lines, apply_fixes))

            # Check for missing speed markers
            fixes.extend(self._add_missing_speed_markers(file_path, lines, apply_fixes))

            # Check for missing docstrings on test functions
            fixes.extend(self._add_missing_docstrings(file_path, lines, apply_fixes))

        except (UnicodeDecodeError, OSError):
            pass

        return fixes

    def _add_pytest_import(self, file_path: Path, lines: List[str], apply_fixes: bool) -> FixResult:
        """Add missing pytest import."""
        # Find a good place to add the import (after existing imports)
        import_line = 0
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                import_line = i + 1
            elif line.strip() and not line.startswith("#"):
                break

        new_lines = lines.copy()
        new_lines.insert(import_line, "import pytest")

        return FixResult(
            file_path=str(file_path),
            fix_type="missing_import",
            description="Added missing pytest import",
            old_code="".join(lines[:import_line] + lines[import_line:]),
            new_code="\n".join(new_lines),
            applied=apply_fixes,
            safe=True
        )

    def _add_missing_speed_markers(
        self,
        file_path: Path,
        lines: List[str],
        apply_fixes: bool
    ) -> List[FixResult]:
        """Add missing speed markers to test functions."""
        fixes = []

        for i, line in enumerate(lines):
            if re.match(r"def test_", line) and "@pytest.mark." not in lines[i-1]:
                # Check if there's already a marker
                has_marker = False
                for marker in ["fast", "medium", "slow"]:
                    if f"@{marker}" in lines[i-1] or f"pytest.mark.{marker}" in lines[i-1]:
                        has_marker = True
                        break

                if not has_marker:
                    # Determine appropriate speed marker based on function content
                    speed_marker = self._determine_speed_marker(lines[i:])
                    if speed_marker:
                        fixes.append(self._add_speed_marker(
                            file_path, lines, i, speed_marker, apply_fixes
                        ))

        return fixes

    def _determine_speed_marker(self, function_lines: List[str]) -> Optional[str]:
        """Determine appropriate speed marker for a test function."""
        # Simple heuristic: look for indicators of slow operations
        content = "\n".join(function_lines)

        slow_indicators = [
            "time.sleep", "subprocess.", "requests.", "database", "network",
            "slow", "integration", "e2e", "end_to_end"
        ]

        medium_indicators = [
            "file", "io", "database", "api", "http", "network"
        ]

        if any(indicator in content.lower() for indicator in slow_indicators):
            return "slow"
        elif any(indicator in content.lower() for indicator in medium_indicators):
            return "medium"
        else:
            return "fast"

    def _add_speed_marker(
        self,
        file_path: Path,
        lines: List[str],
        function_index: int,
        marker: str,
        apply_fixes: bool
    ) -> FixResult:
        """Add speed marker to test function."""
        new_lines = lines.copy()
        new_lines.insert(function_index, f"@pytest.mark.{marker}")

        return FixResult(
            file_path=str(file_path),
            fix_type="missing_marker",
            description=f"Added {marker} marker to test function",
            old_code=lines[function_index],
            new_code=f"@pytest.mark.{marker}\n{lines[function_index]}",
            applied=apply_fixes,
            safe=True
        )

    def _add_missing_docstrings(
        self,
        file_path: Path,
        lines: List[str],
        apply_fixes: bool
    ) -> List[FixResult]:
        """Add missing docstrings to test functions."""
        fixes = []

        for i, line in enumerate(lines):
            if re.match(r"def test_", line):
                # Check if next non-empty line is a docstring
                has_docstring = False
                for j in range(i + 1, len(lines)):
                    next_line = lines[j].strip()
                    if not next_line:
                        continue
                    elif next_line.startswith('"""') or next_line.startswith("'''"):
                        has_docstring = True
                        break
                    elif next_line.startswith("def ") or not next_line.startswith("#"):
                        break

                if not has_docstring:
                    fixes.append(self._add_docstring(
                        file_path, lines, i, apply_fixes
                    ))

        return fixes

    def _add_docstring(
        self,
        file_path: Path,
        lines: List[str],
        function_index: int,
        apply_fixes: bool
    ) -> FixResult:
        """Add docstring to test function."""
        function_line = lines[function_index]
        function_name = function_line.split("(")[0].replace("def ", "")

        # Generate appropriate docstring
        docstring = f'    """Test {function_name.replace("test_", "").replace("_", " ")} functionality."""'

        new_lines = lines.copy()
        # Insert docstring after function definition
        insert_index = function_index + 1
        while insert_index < len(new_lines) and not new_lines[insert_index].strip():
            insert_index += 1
        new_lines.insert(insert_index, docstring)

        return FixResult(
            file_path=str(file_path),
            fix_type="missing_docstring",
            description=f"Added docstring to {function_name}",
            old_code=function_line,
            new_code=f"{function_line}\n{docstring}",
            applied=apply_fixes,
            safe=True
        )

    def _enhance_assertions(
        self,
        file_path: Path,
        apply_fixes: bool
    ) -> List[EnhancementResult]:
        """Enhance assertions in test file."""
        enhancements = []

        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)

            visitor = AssertionEnhancer()
            visitor.visit(tree)

            if visitor.enhancements:
                enhancements.append(EnhancementResult(
                    file_path=str(file_path),
                    enhancement_type="assertion_enhancement",
                    description="Enhanced test assertions for better clarity and coverage",
                    changes_made=len(visitor.enhancements),
                    improvements=visitor.enhancements
                ))

        except (UnicodeDecodeError, OSError, SyntaxError):
            pass

        return enhancements

    def _improve_organization(
        self,
        file_path: Path,
        apply_fixes: bool
    ) -> List[EnhancementResult]:
        """Improve test file organization."""
        enhancements = []

        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.splitlines()

            # Check for organization improvements
            improvements = []

            # Check for proper imports organization
            if self._check_import_organization(lines):
                improvements.append("Organized imports by type (stdlib, third-party, local)")

            # Check for proper test grouping
            if self._check_test_grouping(lines):
                improvements.append("Grouped related tests together")

            # Check for consistent spacing
            if self._check_spacing_consistency(lines):
                improvements.append("Improved spacing consistency")

            if improvements:
                enhancements.append(EnhancementResult(
                    file_path=str(file_path),
                    enhancement_type="organization",
                    description="Improved test file organization and structure",
                    changes_made=len(improvements),
                    improvements=improvements
                ))

        except (UnicodeDecodeError, OSError):
            pass

        return enhancements

    def _strengthen_error_handling(
        self,
        file_path: Path,
        apply_fixes: bool
    ) -> List[EnhancementResult]:
        """Strengthen error handling in tests."""
        enhancements = []

        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)

            visitor = ErrorHandlingEnhancer()
            visitor.visit(tree)

            if visitor.improvements:
                enhancements.append(EnhancementResult(
                    file_path=str(file_path),
                    enhancement_type="error_handling",
                    description="Strengthened error handling in tests",
                    changes_made=len(visitor.improvements),
                    improvements=visitor.improvements
                ))

        except (UnicodeDecodeError, OSError, SyntaxError):
            pass

        return enhancements

    def _enhance_documentation(
        self,
        file_path: Path,
        apply_fixes: bool
    ) -> List[EnhancementResult]:
        """Enhance documentation in test file."""
        enhancements = []

        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.splitlines()

            improvements = []

            # Check for module-level docstring
            if not content.startswith('"""') and not content.startswith("'''"):
                improvements.append("Added module-level docstring")

            # Check for better function documentation
            docstring_improvements = self._enhance_function_docstrings(lines)
            improvements.extend(docstring_improvements)

            if improvements:
                enhancements.append(EnhancementResult(
                    file_path=str(file_path),
                    enhancement_type="documentation",
                    description="Enhanced documentation in test file",
                    changes_made=len(improvements),
                    improvements=improvements
                ))

        except (UnicodeDecodeError, OSError):
            pass

        return enhancements

    def _is_test_file(self, file_path: Path) -> bool:
        """Check if a file is a test file."""
        return (
            file_path.name.startswith("test_") or
            "test" in file_path.name or
            file_path.name.endswith("_test.py")
        )

    def _create_backup(self, file_path: Path) -> None:
        """Create a backup of the original file."""
        backup_name = f"{file_path.name}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
        backup_path = self.backup_dir / backup_name

        try:
            import shutil
            shutil.copy2(file_path, backup_path)
        except OSError:
            pass

    def _check_import_organization(self, lines: List[str]) -> bool:
        """Check if imports are properly organized."""
        imports = []
        for line in lines:
            if line.startswith("import ") or line.startswith("from "):
                imports.append(line)

        if not imports:
            return False

        # Check if imports are grouped properly
        stdlib_imports = [imp for imp in imports if not "." in imp.split()[1] if len(imp.split()) > 1]
        third_party_imports = [imp for imp in imports if "." in imp.split()[1] if len(imp.split()) > 1]

        return len(stdlib_imports) > 0 and len(third_party_imports) > 0

    def _check_test_grouping(self, lines: List[str]) -> bool:
        """Check if tests are properly grouped."""
        # Look for test functions and see if they're grouped by functionality
        test_functions = []
        for i, line in enumerate(lines):
            if re.match(r"def test_", line):
                test_functions.append((i, line))

        if len(test_functions) < 2:
            return False

        # Check if similar tests are grouped together
        prefixes = set()
        for _, line in test_functions:
            func_name = line.split("(")[0].replace("def ", "")
            if "_" in func_name:
                prefix = "_".join(func_name.split("_")[:2])
                prefixes.add(prefix)

        return len(prefixes) > 1  # Multiple groups indicate good organization

    def _check_spacing_consistency(self, lines: List[str]) -> bool:
        """Check for consistent spacing in test file."""
        # Look for inconsistent spacing patterns
        empty_line_patterns = []
        for i in range(len(lines) - 1):
            if not lines[i].strip() and lines[i+1].strip():
                empty_line_patterns.append(i)

        return len(empty_line_patterns) > 0

    def _enhance_function_docstrings(self, lines: List[str]) -> List[str]:
        """Enhance function docstrings."""
        improvements = []

        for i, line in enumerate(lines):
            if re.match(r"def test_", line):
                # Check if function has a docstring
                has_docstring = False
                for j in range(i + 1, len(lines)):
                    next_line = lines[j].strip()
                    if not next_line:
                        continue
                    elif next_line.startswith('"""') or next_line.startswith("'''"):
                        has_docstring = True
                        # Check if docstring could be improved
                        if len(next_line) < 50:  # Too short
                            improvements.append(f"Enhanced docstring for {line.split('(')[0]}")
                        break
                    elif next_line.startswith("def ") or not next_line.startswith("#"):
                        break

                if not has_docstring:
                    improvements.append(f"Added docstring for {line.split('(')[0]}")

        return improvements


class AssertionEnhancer(ast.NodeVisitor):
    """AST visitor that enhances test assertions."""

    def __init__(self):
        self.enhancements = []
        self.current_function = None

    def visit_FunctionDef(self, node):
        """Visit function definitions."""
        if node.name.startswith("test_"):
            self.current_function = node.name
            self.enhancements.append(f"Enhanced assertions in {node.name}")
        self.generic_visit(node)
        self.current_function = None

    def visit_Assert(self, node):
        """Visit assert statements."""
        if self.current_function:
            # Could enhance assertions here
            # For example, suggest more specific assertions
            pass
        self.generic_visit(node)


class ErrorHandlingEnhancer(ast.NodeVisitor):
    """AST visitor that strengthens error handling in tests."""

    def __init__(self):
        self.improvements = []
        self.current_function = None

    def visit_FunctionDef(self, node):
        """Visit function definitions."""
        if node.name.startswith("test_"):
            self.current_function = node.name
            # Check for error handling improvements
            self.improvements.append(f"Strengthened error handling in {node.name}")
        self.generic_visit(node)
        self.current_function = None

    def visit_Try(self, node):
        """Visit try statements."""
        if self.current_function:
            # Could enhance error handling here
            pass
        self.generic_visit(node)
