"""
Unit tests for EnhancedTestCollector

This module contains comprehensive unit tests for the EnhancedTestCollector
class, validating test discovery, categorization, caching, and analysis
capabilities.
"""

import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.testing.enhanced_test_collector import (
    EnhancedTestCollector,
    TestCollectionResult,
    TestInfo,
)


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary test project."""
    project_dir = tmp_path / "test_project"

    # Create test directories
    (project_dir / "tests" / "unit").mkdir(parents=True)
    (project_dir / "tests" / "integration").mkdir(parents=True)
    (project_dir / "tests" / "behavior").mkdir(parents=True)

    # Create unit tests
    (project_dir / "tests" / "unit" / "test_example.py").write_text(
        'import pytest\n\n@pytest.mark.fast\ndef test_example():\n    """Test example function."""\n    assert 1 + 1 == 2\n\n@pytest.mark.medium\ndef test_another_example():\n    """Test another function."""\n    assert True is True'
    )

    # Create integration tests
    (project_dir / "tests" / "integration" / "test_integration.py").write_text(
        'import pytest\n\n@pytest.mark.slow\ndef test_integration():\n    """Test integration functionality."""\n    assert "integration" in "integration test"'
    )

    # Create behavior tests
    (project_dir / "tests" / "behavior" / "features" / "example.feature").write_text(
        "Feature: Example Feature\n  Scenario: Example scenario\n    Given something\n    When I do something\n    Then something should happen"
    )

    return project_dir


@pytest.fixture
def mock_memory_port():
    """Create a mock memory port."""
    mock_port = MagicMock()
    mock_port.store = MagicMock()
    return mock_port


class TestEnhancedTestCollector:
    """Test suite for EnhancedTestCollector."""

    def test_initialization(self):
        """Test collector initialization."""
        collector = EnhancedTestCollector()
        assert collector.cache_dir.exists()
        assert collector.cache_ttl == 300
        assert len(collector.test_patterns) > 0
        assert len(collector.speed_markers) == 3

    def test_initialization_with_memory_port(self, mock_memory_port):
        """Test collector initialization with memory port."""
        collector = EnhancedTestCollector(mock_memory_port)
        assert collector.memory_port == mock_memory_port

    def test_collect_tests_by_category_unit(self, temp_project):
        """Test collecting unit tests."""
        collector = EnhancedTestCollector()
        tests = collector.collect_tests_by_category("unit")

        assert len(tests) > 0
        assert any("test_example.py" in test for test in tests)
        assert any("test_another_example" in test for test in tests)

    def test_collect_tests_by_category_integration(self, temp_project):
        """Test collecting integration tests."""
        collector = EnhancedTestCollector()
        tests = collector.collect_tests_by_category("integration")

        assert len(tests) > 0
        assert any("test_integration.py" in test for test in tests)

    def test_collect_tests_by_category_behavior(self, temp_project):
        """Test collecting behavior tests."""
        collector = EnhancedTestCollector()
        tests = collector.collect_tests_by_category("behavior")

        assert len(tests) > 0
        assert any("example.feature" in test for test in tests)

    def test_collect_tests_by_category_nonexistent(self):
        """Test collecting from nonexistent category."""
        collector = EnhancedTestCollector()
        tests = collector.collect_tests_by_category("nonexistent")

        assert len(tests) == 0

    def test_collect_tests_all_categories(self, temp_project):
        """Test collecting tests from all categories."""
        collector = EnhancedTestCollector()
        all_tests = collector.collect_tests()

        assert "unit" in all_tests
        assert "integration" in all_tests
        assert "behavior" in all_tests
        assert "performance" in all_tests

        assert len(all_tests["unit"]) > 0
        assert len(all_tests["integration"]) > 0
        assert len(all_tests["behavior"]) > 0

    def test_get_tests_with_markers(self, temp_project):
        """Test getting tests with specific markers."""
        collector = EnhancedTestCollector()
        marker_tests = collector.get_tests_with_markers(["fast", "medium", "slow"])

        assert "unit" in marker_tests
        assert "integration" in marker_tests
        assert "behavior" in marker_tests

        # Check that markers are detected
        unit_markers = marker_tests["unit"]
        assert "fast" in unit_markers
        assert "medium" in unit_markers
        assert "slow" in unit_markers

    def test_caching_functionality(self, temp_project):
        """Test caching functionality."""
        collector = EnhancedTestCollector()

        # First call should not use cache
        tests1 = collector.collect_tests_by_category("unit", use_cache=True)

        # Wait a bit to ensure different cache timestamps
        time.sleep(0.1)

        # Second call should use cache
        tests2 = collector.collect_tests_by_category("unit", use_cache=True)

        assert tests1 == tests2

        # Check cache files exist
        cache_files = list(collector.cache_dir.glob("tests_*.json"))
        assert len(cache_files) > 0

    def test_force_refresh_cache(self, temp_project):
        """Test forcing cache refresh."""
        collector = EnhancedTestCollector()

        # First call
        tests1 = collector.collect_tests_by_category("unit", use_cache=True)

        # Wait and force refresh
        time.sleep(0.1)
        tests2 = collector.collect_tests_by_category(
            "unit", use_cache=True, force_refresh=True
        )

        assert tests1 == tests2

    def test_cache_info(self):
        """Test cache information retrieval."""
        collector = EnhancedTestCollector()
        cache_info = collector.get_cache_info()

        assert "cache_files" in cache_info
        assert "total_size_bytes" in cache_info
        assert "cache_dir" in cache_info
        assert "ttl_seconds" in cache_info

    def test_clear_cache(self):
        """Test cache clearing."""
        collector = EnhancedTestCollector()

        # Add some cache files
        collector.collect_tests_by_category("unit", use_cache=True)
        cache_files_before = len(list(collector.cache_dir.glob("tests_*.json")))

        collector.clear_cache()
        cache_files_after = len(list(collector.cache_dir.glob("tests_*.json")))

        assert cache_files_after < cache_files_before

    def test_memory_integration(self, temp_project, mock_memory_port):
        """Test memory system integration."""
        collector = EnhancedTestCollector(mock_memory_port)

        # Collect tests - should store in memory
        tests = collector.collect_tests_by_category("unit")

        # Verify memory store was called
        mock_memory_port.store.assert_called()
        call_args = mock_memory_port.store.call_args

        assert call_args[1]["key"] == "test_collection_unit"
        assert "data" in call_args[1]
        assert "metadata" in call_args[1]

    def test_is_valid_test_file(self, temp_project):
        """Test test file validation."""
        collector = EnhancedTestCollector()

        # Valid test file
        valid_file = temp_project / "tests" / "unit" / "test_example.py"
        assert collector._is_valid_test_file(valid_file)

        # Non-test file
        non_test_file = temp_project / "tests" / "unit" / "not_a_test.py"
        non_test_file.write_text("some_code = 'test'")
        assert not collector._is_valid_test_file(non_test_file)

    def test_contains_test_code(self, temp_project):
        """Test test code detection."""
        collector = EnhancedTestCollector()

        # File with test functions
        test_file = temp_project / "tests" / "unit" / "test_example.py"
        assert collector._contains_test_code(test_file)

        # File without test code
        non_test_file = temp_project / "tests" / "unit" / "utils.py"
        non_test_file.write_text("def utility_function(): pass")
        assert not collector._contains_test_code(non_test_file)

    def test_test_has_marker(self, temp_project):
        """Test marker detection in test files."""
        collector = EnhancedTestCollector()

        # File with fast marker
        fast_file = temp_project / "tests" / "unit" / "test_example.py"
        assert collector._test_has_marker(str(fast_file), "fast")

        # File without medium marker
        assert not collector._test_has_marker(str(fast_file), "medium")

    def test_analyze_markers(self, temp_project):
        """Test marker analysis."""
        collector = EnhancedTestCollector()

        test_files = [
            str(temp_project / "tests" / "unit" / "test_example.py"),
            str(temp_project / "tests" / "integration" / "test_integration.py"),
        ]

        marker_counts = collector._analyze_markers(test_files)

        assert marker_counts["fast"] > 0
        assert marker_counts["slow"] > 0
        assert marker_counts["medium"] >= 0

    def test_cache_operations(self):
        """Test cache save and load operations."""
        collector = EnhancedTestCollector()

        # Save to cache
        test_data = ["test1.py", "test2.py"]
        collector._save_to_cache("test_key", test_data)

        # Load from cache
        loaded_data = collector._get_from_cache("test_key")

        assert loaded_data == test_data

    def test_cache_expiration(self):
        """Test cache expiration."""
        collector = EnhancedTestCollector()

        # Save to cache
        test_data = ["test1.py", "test2.py"]
        collector._save_to_cache("test_key", test_data)

        # Modify cache file timestamp to make it expired
        cache_file = collector.cache_dir / "test_key.json"
        if cache_file.exists():
            # Set modification time to past (more than TTL)
            past_time = time.time() - (collector.cache_ttl + 10)
            os.utime(cache_file, (past_time, past_time))

        # Try to load (should return None due to expiration)
        loaded_data = collector._get_from_cache("test_key")
        assert loaded_data is None

    def test_store_collection_results(self, temp_project, mock_memory_port):
        """Test storing collection results in memory."""
        collector = EnhancedTestCollector(mock_memory_port)

        # Collect tests and store results
        tests = ["test1.py", "test2.py"]
        collection_time = 1.5

        collector._store_collection_results("unit", tests, collection_time)

        # Verify memory store was called with correct data
        mock_memory_port.store.assert_called_once()
        call_args = mock_memory_port.store.call_args

        assert call_args[1]["key"] == "test_collection_unit"
        assert "data" in call_args[1]
        assert "metadata" in call_args[1]
        assert call_args[1]["metadata"]["category"] == "unit"

    def test_nonexistent_directory(self):
        """Test handling of nonexistent directories."""
        collector = EnhancedTestCollector()

        tests = collector.collect_tests_by_category("nonexistent")
        assert len(tests) == 0

        isolation_report = collector._isolation_analyzer.analyze_test_isolation(
            "nonexistent"
        )
        assert isolation_report.total_issues == 0
        assert isolation_report.files_analyzed == 0

    def test_cache_file_corruption(self):
        """Test handling of corrupted cache files."""
        collector = EnhancedTestCollector()

        # Create corrupted cache file
        cache_file = collector.cache_dir / "tests_unit.json"
        cache_file.write_text("invalid json content")

        # Should handle gracefully
        loaded_data = collector._get_from_cache("tests_unit")
        assert loaded_data is None

        # Cache file should be cleaned up
        assert not cache_file.exists()


class TestTestCollectionResult:
    """Test suite for TestCollectionResult dataclass."""

    def test_creation(self):
        """Test TestCollectionResult creation."""
        result = TestCollectionResult(
            tests={"unit": ["test1.py"]},
            collection_time=1.5,
            total_tests=1,
            categories={"unit": 1},
            markers={"fast": 1},
        )

        assert result.total_tests == 1
        assert result.collection_time == 1.5
        assert result.categories["unit"] == 1
        assert result.markers["fast"] == 1
        assert result.cache_used is False

    def test_as_dict(self):
        """Test conversion to dictionary."""
        result = TestCollectionResult(
            tests={"unit": ["test1.py"]},
            collection_time=1.5,
            total_tests=1,
            categories={"unit": 1},
            markers={"fast": 1},
        )

        result_dict = result.__dict__
        assert result_dict["total_tests"] == 1
        assert result_dict["collection_time"] == 1.5


class TestTestInfo:
    """Test suite for TestInfo dataclass."""

    def test_creation(self):
        """Test TestInfo creation."""
        info = TestInfo(
            name="test_example",
            file_path="tests/unit/test_example.py",
            line_number=5,
            markers={"fast"},
        )

        assert info.name == "test_example"
        assert info.file_path == "tests/unit/test_example.py"
        assert info.line_number == 5
        assert "fast" in info.markers
        assert info.docstring is None
        assert info.is_async is False
        assert len(info.parameters) == 0

    def test_with_docstring(self):
        """Test TestInfo with docstring."""
        info = TestInfo(
            name="test_example",
            file_path="tests/unit/test_example.py",
            line_number=5,
            markers={"fast"},
            docstring="Test example function",
        )

        assert info.docstring == "Test example function"


class TestCacheOperations:
    """Test suite for cache operations."""

    def test_cache_directory_creation(self):
        """Test that cache directory is created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir) / "cache"
            collector = EnhancedTestCollector()
            collector.cache_dir = cache_dir

            # Cache directory should be created
            assert cache_dir.exists()

    def test_cache_ttl_configuration(self):
        """Test cache TTL configuration."""
        collector = EnhancedTestCollector()
        assert collector.cache_ttl == 300

        # Test with custom TTL
        collector.cache_ttl = 600
        assert collector.cache_ttl == 600


class TestErrorHandling:
    """Test suite for error handling."""

    def test_unicode_decode_error(self):
        """Test handling of unicode decode errors."""
        collector = EnhancedTestCollector()

        # Create a file with invalid encoding
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(b"\xff\xfe\x00\x00")  # Invalid UTF-8
            invalid_file = f.name

        try:
            # Should handle gracefully
            assert not collector._is_valid_test_file(Path(invalid_file))
            assert not collector._contains_test_code(Path(invalid_file))
            assert not collector._test_has_marker(invalid_file, "fast")
        finally:
            os.unlink(invalid_file)

    def test_os_error_handling(self):
        """Test handling of OS errors."""
        collector = EnhancedTestCollector()

        # Try to read from a directory (should fail)
        assert not collector._is_valid_test_file(
            Path("/root")
        )  # Permission denied on most systems

        # Try to access non-existent file
        assert not collector._test_has_marker("/nonexistent/file.py", "fast")

    def test_memory_storage_failure(self, mock_memory_port):
        """Test handling of memory storage failures."""
        collector = EnhancedTestCollector(mock_memory_port)

        # Make memory storage fail
        mock_memory_port.store.side_effect = Exception("Storage failed")

        # Should not raise exception, just continue
        tests = collector.collect_tests_by_category("unit")
        assert isinstance(tests, list)
