import pytest
from unittest.mock import MagicMock, patch

from devsynth.application.edrr.templates import (
    EXPAND_PHASE_TEMPLATE,
    DIFFERENTIATE_PHASE_TEMPLATE,
    REFINE_PHASE_TEMPLATE,
    RETROSPECT_PHASE_TEMPLATE,
    register_edrr_templates
)
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.methodology.base import Phase


class TestEDRRTemplates:
    """Tests for the EDRR templates module."""

    def test_template_definitions(self):
        """Test that all templates are properly defined."""
        # Verify that all templates are defined and are strings
        assert isinstance(EXPAND_PHASE_TEMPLATE, str)
        assert isinstance(DIFFERENTIATE_PHASE_TEMPLATE, str)
        assert isinstance(REFINE_PHASE_TEMPLATE, str)
        assert isinstance(RETROSPECT_PHASE_TEMPLATE, str)

        # Verify that templates contain expected content
        assert "Expand Phase for Task" in EXPAND_PHASE_TEMPLATE
        assert "Generate diverse ideas" in EXPAND_PHASE_TEMPLATE

        assert "Differentiate Phase for Task" in DIFFERENTIATE_PHASE_TEMPLATE
        assert "Analyze and compare" in DIFFERENTIATE_PHASE_TEMPLATE

        assert "Refine Phase for Task" in REFINE_PHASE_TEMPLATE
        assert "Elaborate on the selected approach" in REFINE_PHASE_TEMPLATE

        assert "Retrospect Phase for Task" in RETROSPECT_PHASE_TEMPLATE
        assert "Extract learnings" in RETROSPECT_PHASE_TEMPLATE

        # Verify that templates can be formatted with task description
        task_description = "Test task description"
        formatted_expand = EXPAND_PHASE_TEMPLATE.format(task_description=task_description)
        assert task_description in formatted_expand

        formatted_differentiate = DIFFERENTIATE_PHASE_TEMPLATE.format(task_description=task_description)
        assert task_description in formatted_differentiate

        formatted_refine = REFINE_PHASE_TEMPLATE.format(task_description=task_description)
        assert task_description in formatted_refine

        formatted_retrospect = RETROSPECT_PHASE_TEMPLATE.format(task_description=task_description)
        assert task_description in formatted_retrospect

    def test_register_edrr_templates(self):
        """Test that templates are correctly registered with the prompt manager."""
        # Create a mock prompt manager
        mock_prompt_manager = MagicMock(spec=PromptManager)

        # Call the function under test
        register_edrr_templates(mock_prompt_manager)

        # Verify that register_template was called for each template
        assert mock_prompt_manager.register_template.call_count == 4

        # Verify the calls for each template
        mock_prompt_manager.register_template.assert_any_call(
            name="expand_phase",
            description="Template for the Expand phase of the EDRR cycle",
            template_text=EXPAND_PHASE_TEMPLATE,
            edrr_phase="EXPAND"
        )

        mock_prompt_manager.register_template.assert_any_call(
            name="differentiate_phase",
            description="Template for the Differentiate phase of the EDRR cycle",
            template_text=DIFFERENTIATE_PHASE_TEMPLATE,
            edrr_phase="DIFFERENTIATE"
        )

        mock_prompt_manager.register_template.assert_any_call(
            name="refine_phase",
            description="Template for the Refine phase of the EDRR cycle",
            template_text=REFINE_PHASE_TEMPLATE,
            edrr_phase="REFINE"
        )

        mock_prompt_manager.register_template.assert_any_call(
            name="retrospect_phase",
            description="Template for the Retrospect phase of the EDRR cycle",
            template_text=RETROSPECT_PHASE_TEMPLATE,
            edrr_phase="RETROSPECT"
        )

    def test_register_edrr_templates_error_handling(self):
        """Test that errors are handled appropriately when registering templates."""
        # Create a mock prompt manager that raises ValueError
        mock_prompt_manager = MagicMock(spec=PromptManager)
        mock_prompt_manager.register_template.side_effect = ValueError("Template already registered")

        # Mock the logger to verify it's called
        with patch("devsynth.application.edrr.templates.logger") as mock_logger:
            # Call the function under test
            register_edrr_templates(mock_prompt_manager)

            # Verify that the warning was logged
            mock_logger.warning.assert_called_once()
            assert "Error registering EDRR templates" in mock_logger.warning.call_args[0][0]

    @pytest.mark.parametrize("phase,template", [
        (Phase.EXPAND, EXPAND_PHASE_TEMPLATE),
        (Phase.DIFFERENTIATE, DIFFERENTIATE_PHASE_TEMPLATE),
        (Phase.REFINE, REFINE_PHASE_TEMPLATE),
        (Phase.RETROSPECT, RETROSPECT_PHASE_TEMPLATE)
    ])
    def test_template_for_each_phase(self, phase, template):
        """Test that there is a template for each EDRR phase."""
        # This test uses parameterization to verify that each phase has a corresponding template
        assert template is not None
        assert isinstance(template, str)
        assert len(template) > 0
