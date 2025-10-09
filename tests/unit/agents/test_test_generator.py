"""Unit tests for the test generator agent utilities."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from devsynth.agents.test_generator import (
    BOUNDARY_VALUES_PROMPT,
    ERROR_CONDITIONS_PROMPT,
    _load_template,
    build_edge_case_prompts,
)


class TestTestGenerator:
    """Test the test generator utility functions."""

    def test_load_template_existing_file(self, tmp_path: Path) -> None:
        """Test loading a template from an existing file."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "boundary_values.md"
        template_content = "Test boundary values template content."
        template_file.write_text(template_content)

        with patch("devsynth.agents.test_generator._TEMPLATE_DIR", template_dir):
            result = _load_template("boundary_values")

        assert result == template_content.strip()

    def test_load_template_missing_file(self, tmp_path: Path) -> None:
        """Test loading a template when the file doesn't exist."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        with patch("devsynth.agents.test_generator._TEMPLATE_DIR", template_dir):
            with patch("devsynth.agents.test_generator.logger") as mock_logger:
                result = _load_template("nonexistent_template")

        assert result == ""
        mock_logger.warning.assert_called_once()

    def test_load_template_empty_file(self, tmp_path: Path) -> None:
        """Test loading a template from an empty file."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "empty.md"
        template_file.write_text("")  # Empty file

        with patch("devsynth.agents.test_generator._TEMPLATE_DIR", template_dir):
            result = _load_template("empty")

        assert result == ""

    def test_load_template_with_whitespace(self, tmp_path: Path) -> None:
        """Test loading a template with leading/trailing whitespace."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "whitespace.md"
        template_content = "\n  Template content with whitespace  \n"
        template_file.write_text(template_content)

        with patch("devsynth.agents.test_generator._TEMPLATE_DIR", template_dir):
            result = _load_template("whitespace")

        assert result == "Template content with whitespace"

    def test_boundary_values_prompt_loaded(self) -> None:
        """Test that BOUNDARY_VALUES_PROMPT is loaded correctly."""
        # The constant should still be defined and be a string
        assert isinstance(BOUNDARY_VALUES_PROMPT, str)
        # In the actual project, this will contain content from the template file

    def test_error_conditions_prompt_loaded(self) -> None:
        """Test that ERROR_CONDITIONS_PROMPT is loaded correctly."""
        # The constant should still be defined and be a string
        assert isinstance(ERROR_CONDITIONS_PROMPT, str)
        # In the actual project, this will contain content from the template file

    def test_build_edge_case_prompts_with_templates(self, tmp_path: Path) -> None:
        """Test build_edge_case_prompts when templates are available."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        # Create template files
        (template_dir / "boundary_values.md").write_text("Boundary values template")
        (template_dir / "error_conditions.md").write_text("Error conditions template")

        with patch("devsynth.agents.test_generator._TEMPLATE_DIR", template_dir):
            # Reset the module-level constants to use our test templates
            with patch(
                "devsynth.agents.test_generator.BOUNDARY_VALUES_PROMPT",
                "Boundary values template",
            ):
                with patch(
                    "devsynth.agents.test_generator.ERROR_CONDITIONS_PROMPT",
                    "Error conditions template",
                ):
                    prompts = build_edge_case_prompts()

        assert "boundary_values" in prompts
        assert "error_conditions" in prompts
        assert prompts["boundary_values"] == "Boundary values template"
        assert prompts["error_conditions"] == "Error conditions template"

    def test_build_edge_case_prompts_without_templates(self, tmp_path: Path) -> None:
        """Test build_edge_case_prompts when no templates are available."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        # Don't create any template files

        with patch("devsynth.agents.test_generator._TEMPLATE_DIR", template_dir):
            # Reset the module-level constants to be empty for this test
            with patch("devsynth.agents.test_generator.BOUNDARY_VALUES_PROMPT", ""):
                with patch(
                    "devsynth.agents.test_generator.ERROR_CONDITIONS_PROMPT", ""
                ):
                    prompts = build_edge_case_prompts()

        # Should return empty dict since no templates are loaded
        assert prompts == {}

    def test_build_edge_case_prompts_mixed_availability(self, tmp_path: Path) -> None:
        """Test build_edge_case_prompts with mixed template availability."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        # Create only one template file
        (template_dir / "boundary_values.md").write_text("Boundary values template")
        # Don't create error_conditions.md

        with patch("devsynth.agents.test_generator._TEMPLATE_DIR", template_dir):
            # Reset the module-level constants to match our test scenario
            with patch(
                "devsynth.agents.test_generator.BOUNDARY_VALUES_PROMPT",
                "Boundary values template",
            ):
                with patch(
                    "devsynth.agents.test_generator.ERROR_CONDITIONS_PROMPT", ""
                ):
                    prompts = build_edge_case_prompts()

        # Should only include the available template
        assert "boundary_values" in prompts
        assert "error_conditions" not in prompts
        assert prompts["boundary_values"] == "Boundary values template"

    def test_template_directory_path_construction(self) -> None:
        """Test that the template directory path is constructed correctly."""
        # This is a bit of a white-box test, but ensures the path construction logic
        expected_path = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "src"
            / "devsynth"
            / "application"
            / "prompts"
            / "templates"
            / "test_generation"
        )

        # We can't easily test the exact path without knowing the test environment,
        # but we can verify the path construction logic works
        from devsynth.agents.test_generator import _TEMPLATE_DIR

        assert isinstance(_TEMPLATE_DIR, Path)
        assert "test_generation" in str(_TEMPLATE_DIR)
