"""
Unit tests for the test templates location.

This test verifies that the test templates can be used to create new tests.
It creates a temporary templates directory structure for testing.
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest


class TestTemplateLocation:
    """Test suite for the test templates location.

    ReqID: N/A"""

    @pytest.fixture
    def setup_template_dir(self):
        """Create a temporary templates directory structure for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            templates_dir = Path(temp_dir) / ".devsynth" / "templates" / "tests"
            os.makedirs(templates_dir / "unit", exist_ok=True)
            os.makedirs(templates_dir / "integration", exist_ok=True)
            os.makedirs(templates_dir / "behavior", exist_ok=True)
            unit_template = templates_dir / "unit" / "test_template.py"
            with open(unit_template, "w") as f:
                f.write(
                    """""\"
Unit Test Template for DevSynth
""\"

import pytest

def test_example():
    ""\"Example test.""\"
    assert True"""
                )
            integration_template = (
                templates_dir / "integration" / "test_integration_template.py"
            )
            with open(integration_template, "w") as f:
                f.write(
                    """""\"
Integration Test Template for DevSynth
""\"

import pytest

def test_integration_example():
    ""\"Example integration test.""\"
    assert True"""
                )
            feature_template = templates_dir / "behavior" / "feature_template.feature"
            with open(feature_template, "w") as f:
                f.write(
                    """Feature: Example Feature
  Scenario: Example Scenario
    Given a condition
    When an action occurs
    Then a result is expected"""
                )
            steps_template = templates_dir / "behavior" / "test_steps_template.py"
            with open(steps_template, "w") as f:
                f.write(
                    """""\"
BDD Steps Template for DevSynth
""\"

import pytest
from pytest_bdd import given, when, then, scenarios

scenarios("feature_template.feature")"""
                )
            readme_path = templates_dir / "README.md"
            with open(readme_path, "w") as f:
                f.write(
                    """# Test Templates for DevSynth

This directory contains templates for different types of tests."""
                )
            yield templates_dir

    @pytest.mark.fast
    def test_templates_exist_in_temp_location_succeeds(self, setup_template_dir):
        """Test that the templates exist in the temporary location.

        ReqID: N/A"""
        templates_dir = setup_template_dir
        assert (
            templates_dir / "unit"
        ).exists(), "Unit templates directory does not exist"
        assert (
            templates_dir / "integration"
        ).exists(), "Integration templates directory does not exist"
        assert (
            templates_dir / "behavior"
        ).exists(), "Behavior templates directory does not exist"
        assert (
            templates_dir / "unit" / "test_template.py"
        ).exists(), "Unit test template does not exist"
        assert (
            templates_dir / "integration" / "test_integration_template.py"
        ).exists(), "Integration test template does not exist"
        assert (
            templates_dir / "behavior" / "feature_template.feature"
        ).exists(), "Feature template does not exist"
        assert (
            templates_dir / "behavior" / "test_steps_template.py"
        ).exists(), "Step definitions template does not exist"
        assert (templates_dir / "README.md").exists(), "README.md does not exist"

    @pytest.mark.fast
    def test_can_use_template_to_create_test_succeeds(self, setup_template_dir):
        """Test that a template can be used to create a new test file.

        ReqID: N/A"""
        templates_dir = setup_template_dir
        with tempfile.TemporaryDirectory() as test_dir:
            template_path = templates_dir / "unit" / "test_template.py"
            test_path = Path(test_dir) / "test_example.py"
            shutil.copy(template_path, test_path)
            assert test_path.exists(), "Failed to create test file from template"
            with open(test_path) as f:
                content = f.read()
                assert (
                    "Unit Test Template for DevSynth" in content
                ), "Template content not found in created file"
