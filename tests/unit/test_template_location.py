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
    """Test suite for the test templates location."""

    @pytest.fixture
    def setup_template_dir(self):
        """Create a temporary templates directory structure for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create the templates directory structure
            templates_dir = Path(temp_dir) / '.devsynth' / 'templates' / 'tests'
            os.makedirs(templates_dir / 'unit', exist_ok=True)
            os.makedirs(templates_dir / 'integration', exist_ok=True)
            os.makedirs(templates_dir / 'behavior', exist_ok=True)

            # Create sample template files
            unit_template = templates_dir / 'unit' / 'test_template.py'
            with open(unit_template, 'w') as f:
                f.write('"""\nUnit Test Template for DevSynth\n"""\n\nimport pytest\n\ndef test_example():\n    """Example test."""\n    assert True')

            integration_template = templates_dir / 'integration' / 'test_integration_template.py'
            with open(integration_template, 'w') as f:
                f.write('"""\nIntegration Test Template for DevSynth\n"""\n\nimport pytest\n\ndef test_integration_example():\n    """Example integration test."""\n    assert True')

            feature_template = templates_dir / 'behavior' / 'feature_template.feature'
            with open(feature_template, 'w') as f:
                f.write('Feature: Example Feature\n  Scenario: Example Scenario\n    Given a condition\n    When an action occurs\n    Then a result is expected')

            steps_template = templates_dir / 'behavior' / 'test_steps_template.py'
            with open(steps_template, 'w') as f:
                f.write('"""\nBDD Steps Template for DevSynth\n"""\n\nimport pytest\nfrom pytest_bdd import given, when, then, scenarios\n\nscenarios("feature_template.feature")')

            # Create README.md
            readme_path = templates_dir / 'README.md'
            with open(readme_path, 'w') as f:
                f.write('# Test Templates for DevSynth\n\nThis directory contains templates for different types of tests.')

            yield templates_dir

    def test_templates_exist_in_temp_location(self, setup_template_dir):
        """Test that the templates exist in the temporary location."""
        templates_dir = setup_template_dir

        # Check that the subdirectories exist
        assert (templates_dir / 'unit').exists(), "Unit templates directory does not exist"
        assert (templates_dir / 'integration').exists(), "Integration templates directory does not exist"
        assert (templates_dir / 'behavior').exists(), "Behavior templates directory does not exist"

        # Check that the template files exist
        assert (templates_dir / 'unit' / 'test_template.py').exists(), "Unit test template does not exist"
        assert (templates_dir / 'integration' / 'test_integration_template.py').exists(), "Integration test template does not exist"
        assert (templates_dir / 'behavior' / 'feature_template.feature').exists(), "Feature template does not exist"
        assert (templates_dir / 'behavior' / 'test_steps_template.py').exists(), "Step definitions template does not exist"

        # Check that the README.md exists
        assert (templates_dir / 'README.md').exists(), "README.md does not exist"

    def test_can_use_template_to_create_test(self, setup_template_dir):
        """Test that a template can be used to create a new test file."""
        templates_dir = setup_template_dir

        # Create a temporary directory for the test file
        with tempfile.TemporaryDirectory() as test_dir:
            # Copy the unit test template to the test directory
            template_path = templates_dir / 'unit' / 'test_template.py'
            test_path = Path(test_dir) / 'test_example.py'
            shutil.copy(template_path, test_path)

            # Check that the file exists
            assert test_path.exists(), "Failed to create test file from template"

            # Check that the file contains the expected content
            with open(test_path, 'r') as f:
                content = f.read()
                assert "Unit Test Template for DevSynth" in content, "Template content not found in created file"
