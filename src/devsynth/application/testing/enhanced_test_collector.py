"""
Enhanced Test Collector

This module provides sophisticated test collection and analysis capabilities that extend
beyond basic pytest integration. It includes advanced test discovery, categorization,
and analysis features for comprehensive test management.

Key features:
- Enhanced test discovery with caching and performance optimization
- Test isolation analysis and dependency detection
- Marker-based categorization and filtering
- Integration with DevSynth's memory system for persistent analysis
"""

import ast
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field  # type: ignore[attr-defined]
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

try:
    from devsynth.ports.memory_port import MemoryPort
except ImportError:
    # Optional import - memory system may not be available
    MemoryPort = type(None)  # type: ignore[assignment,misc]


@dataclass
class TestInfo:
    """Information about a test function or method."""

    name: str
    file_path: str
    line_number: int
    markers: set[str]
    docstring: str | None = None
    is_async: bool = False
    parameters: list[str] = field(default_factory=list)
    dependencies: set[str] = field(default_factory=set)


@dataclass
class TestCollectionResult:
    """Result of test collection operation."""

    tests: dict[str, list[TestInfo]]
    collection_time: float
    total_tests: int
    categories: dict[str, int]
    markers: dict[str, int]
    cache_used: bool = False


@dataclass
class IsolationIssue:
    """Represents a test isolation issue."""

    file_path: str
    line_number: int
    issue_type: str
    severity: str
    description: str
    suggestion: str


@dataclass
class IsolationReport:
    """Report of test isolation analysis."""

    total_issues: int
    issues_by_severity: dict[str, int]
    issues_by_type: dict[str, int]
    issues: list[IsolationIssue]
    analysis_time: float
    files_analyzed: int


class EnhancedTestCollector:
    """
    Enhanced test collector with advanced analysis capabilities.

    This class provides sophisticated test discovery, categorization, and analysis
    that extends beyond basic pytest collection. It includes caching, performance
    optimization, and integration with DevSynth's memory system.
    """

    def __init__(self, memory_port: Any = None):
        """Initialize the enhanced test collector."""
        self.memory_port = memory_port
        self.cache_dir = Path.home() / ".devsynth" / "test_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = 300  # 5 minutes

        # Common test patterns and markers
        self.test_patterns = [
            r"def test_.*\(",
            r"def .*test.*\(",
            r"class.*Test.*:",
            r"class.*Suite.*:",
        ]

        self.speed_markers = {"fast", "medium", "slow"}
        self.category_markers = {"unit", "integration", "behavior", "performance"}

    def collect_tests_by_category(
        self, category: str, use_cache: bool = True, force_refresh: bool = False
    ) -> list[str]:
        """
        Collect tests by category using enhanced parsing.

        Args:
            category: Test category (unit, integration, behavior, etc.)
            use_cache: Whether to use cached results
            force_refresh: Whether to force cache refresh

        Returns:
            List of test file paths
        """
        start_time = time.time()

        # Check cache first
        cache_key = f"tests_{category}"
        if use_cache and not force_refresh:
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return cached_result

        # Define category directories
        category_dirs = {
            "unit": "tests/unit",
            "integration": "tests/integration",
            "behavior": "tests/behavior",
            "performance": "tests/performance",
        }

        directory = category_dirs.get(category, f"tests/{category}")

        if category == "behavior":
            # Use existing behavior test collection for BDD features
            tests = self._collect_behavior_tests(directory)
        else:
            # Use enhanced collection for other test types
            tests = self._collect_enhanced_tests(directory)

        # Cache the results
        if use_cache:
            self._save_to_cache(cache_key, tests)

        collection_time = time.time() - start_time

        # Store in memory if available
        if self.memory_port:
            self._store_collection_results(category, tests, collection_time)

        return tests

    def collect_tests(self, use_cache: bool = True) -> dict[str, list[str]]:
        """
        Collect all tests organized by category.

        Args:
            use_cache: Whether to use cached results

        Returns:
            Dictionary mapping categories to lists of test paths
        """
        categories = ["unit", "integration", "behavior", "performance"]
        results = {}

        for category in categories:
            results[category] = self.collect_tests_by_category(category, use_cache)

        return results

    def get_tests_with_markers(
        self, marker_types: list[str] | None = None, use_cache: bool = True
    ) -> dict[str, dict[str, list[str]]]:
        """
        Get tests with specific markers organized by category.

        Args:
            marker_types: List of marker types to check for
            use_cache: Whether to use cached results

        Returns:
            Dictionary mapping categories to marker dictionaries
        """
        if marker_types is None:
            marker_types = ["fast", "medium", "slow"]

        results = {}

        # Collect tests for each category
        for category in ["unit", "integration", "behavior", "performance"]:
            category_tests = self.collect_tests_by_category(category, use_cache)
            marker_results = {}

            for marker in marker_types:
                # Find tests with the specific marker
                tests_with_marker = []
                for test_file in category_tests:
                    if self._test_has_marker(test_file, marker):
                        tests_with_marker.append(test_file)
                marker_results[marker] = tests_with_marker

            results[category] = marker_results

        return results

    def _collect_behavior_tests(self, directory: str) -> list[str]:
        """Collect behavior tests (BDD feature files)."""
        behavior_dir = Path(directory)
        if not behavior_dir.exists():
            return []

        feature_files = list(behavior_dir.rglob("*.feature"))
        return [str(f) for f in feature_files]

    def _collect_enhanced_tests(self, directory: str) -> list[str]:
        """Collect enhanced tests with advanced analysis."""
        test_dir = Path(directory)
        if not test_dir.exists():
            return []

        test_files = []

        # Walk through directory and find Python test files
        for py_file in test_dir.rglob("test_*.py"):
            if self._is_valid_test_file(py_file):
                test_files.append(str(py_file))

        # Also look for files containing test classes or functions
        for py_file in test_dir.rglob("*.py"):
            if py_file.name.startswith("test_"):
                continue  # Already added above

            if self._contains_test_code(py_file):
                test_files.append(str(py_file))

        return sorted(test_files)

    def _is_valid_test_file(self, file_path: Path) -> bool:
        """Check if a file is a valid test file."""
        try:
            content = file_path.read_text(encoding="utf-8")

            # Check for pytest imports or test markers
            has_pytest_import = "import pytest" in content or "from pytest" in content

            # Check for test functions or classes
            has_test_functions = any(
                re.search(pattern, content) for pattern in self.test_patterns
            )

            # Check for test markers
            has_markers = any(marker in content for marker in self.speed_markers)

            return has_pytest_import or has_test_functions or has_markers

        except (UnicodeDecodeError, OSError):
            return False

    def _contains_test_code(self, file_path: Path) -> bool:
        """Check if a file contains test code."""
        try:
            content = file_path.read_text(encoding="utf-8")
            return any(re.search(pattern, content) for pattern in self.test_patterns)
        except (UnicodeDecodeError, OSError):
            return False

    def _test_has_marker(self, test_file: str, marker: str) -> bool:
        """Check if a test file has a specific marker."""
        try:
            content = Path(test_file).read_text(encoding="utf-8")
            return f"@{marker}" in content or f"pytest.mark.{marker}" in content
        except (UnicodeDecodeError, OSError):
            return False

    def _get_from_cache(self, key: str) -> list[str] | None:
        """Get data from cache if available and not expired."""
        cache_file = self.cache_dir / f"{key}.json"

        if not cache_file.exists():
            return None

        try:
            # Check if cache is expired
            cache_age = time.time() - cache_file.stat().st_mtime
            if cache_age > self.cache_ttl:
                cache_file.unlink()
                return None

            with open(cache_file) as f:
                data = json.load(f)

            return data.get("tests", [])  # type: ignore[no-any-return]

        except (json.JSONDecodeError, OSError):
            cache_file.unlink()
            return None

    def _save_to_cache(self, key: str, tests: list[str]) -> None:
        """Save data to cache."""
        cache_file = self.cache_dir / f"{key}.json"

        try:
            data = {"tests": tests, "timestamp": time.time(), "count": len(tests)}

            with open(cache_file, "w") as f:
                json.dump(data, f, indent=2)

        except OSError:
            # Cache write failed, but don't fail the operation
            pass

    def _store_collection_results(
        self, category: str, tests: list[str], collection_time: float
    ) -> None:
        """Store collection results in memory system."""
        if not self.memory_port:
            return

        try:
            memory_key = f"test_collection_{category}"
            result = TestCollectionResult(
                tests={category: tests},  # type: ignore[dict-item]
                collection_time=collection_time,
                total_tests=len(tests),
                categories={category: len(tests)},
                markers=self._analyze_markers(tests),
            )

            self.memory_port.store(
                key=memory_key,
                data=result.__dict__,
                metadata={"type": "test_collection", "category": category},
            )

        except Exception:
            # Memory storage failed, but don't fail the operation
            pass

    def _analyze_markers(self, test_files: list[str]) -> dict[str, int]:
        """Analyze markers in test files."""
        marker_counts = {marker: 0 for marker in self.speed_markers}

        for test_file in test_files:
            for marker in self.speed_markers:
                if self._test_has_marker(test_file, marker):
                    marker_counts[marker] += 1

        return marker_counts

    def clear_cache(self) -> None:
        """Clear the test collection cache."""
        try:
            for cache_file in self.cache_dir.glob("tests_*.json"):
                cache_file.unlink()
        except OSError:
            pass

    def get_cache_info(self) -> dict[str, Any]:
        """Get information about the cache."""
        cache_files = list(self.cache_dir.glob("tests_*.json"))
        total_size = sum(f.stat().st_size for f in cache_files if f.exists())

        return {
            "cache_files": len(cache_files),
            "total_size_bytes": total_size,
            "cache_dir": str(self.cache_dir),
            "ttl_seconds": self.cache_ttl,
        }
