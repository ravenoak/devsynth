import pytest
from unittest.mock import MagicMock, patch
from devsynth.application.edrr.templates import EXPAND_PHASE_TEMPLATE, DIFFERENTIATE_PHASE_TEMPLATE, REFINE_PHASE_TEMPLATE, RETROSPECT_PHASE_TEMPLATE, register_edrr_templates
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.methodology.base import Phase

class TestEDRRTemplates:
    """Tests for the EDRR templates module.

ReqID: N/A"""

    @pytest.mark.medium
    def test_template_definitions_succeeds(self):
        """Test that all templates are properly defined.

ReqID: N/A"""
        assert isinstance(EXPAND_PHASE_TEMPLATE, str)
        assert isinstance(DIFFERENTIATE_PHASE_TEMPLATE, str)
        assert isinstance(REFINE_PHASE_TEMPLATE, str)
        assert isinstance(RETROSPECT_PHASE_TEMPLATE, str)
        assert 'Expand Phase for Task' in EXPAND_PHASE_TEMPLATE
        assert 'Generate diverse ideas' in EXPAND_PHASE_TEMPLATE
        assert 'Differentiate Phase for Task' in DIFFERENTIATE_PHASE_TEMPLATE
        assert 'Analyze and compare' in DIFFERENTIATE_PHASE_TEMPLATE
        assert 'Refine Phase for Task' in REFINE_PHASE_TEMPLATE
        assert 'Elaborate on the selected approach' in REFINE_PHASE_TEMPLATE
        assert 'Retrospect Phase for Task' in RETROSPECT_PHASE_TEMPLATE
        assert 'Extract learnings' in RETROSPECT_PHASE_TEMPLATE
        task_description = 'Test task description'
        formatted_expand = EXPAND_PHASE_TEMPLATE.format(task_description=task_description)
        assert task_description in formatted_expand
        formatted_differentiate = DIFFERENTIATE_PHASE_TEMPLATE.format(task_description=task_description)
        assert task_description in formatted_differentiate
        formatted_refine = REFINE_PHASE_TEMPLATE.format(task_description=task_description)
        assert task_description in formatted_refine
        formatted_retrospect = RETROSPECT_PHASE_TEMPLATE.format(task_description=task_description)
        assert task_description in formatted_retrospect

    @pytest.mark.medium
    def test_register_edrr_templates_succeeds(self):
        """Test that templates are correctly registered with the prompt manager.

ReqID: N/A"""
        mock_prompt_manager = MagicMock(spec=PromptManager)
        register_edrr_templates(mock_prompt_manager)
        assert mock_prompt_manager.register_template.call_count == 4
        mock_prompt_manager.register_template.assert_any_call(name='expand_phase', description='Template for the Expand phase of the EDRR cycle', template_text=EXPAND_PHASE_TEMPLATE, edrr_phase='EXPAND')
        mock_prompt_manager.register_template.assert_any_call(name='differentiate_phase', description='Template for the Differentiate phase of the EDRR cycle', template_text=DIFFERENTIATE_PHASE_TEMPLATE, edrr_phase='DIFFERENTIATE')
        mock_prompt_manager.register_template.assert_any_call(name='refine_phase', description='Template for the Refine phase of the EDRR cycle', template_text=REFINE_PHASE_TEMPLATE, edrr_phase='REFINE')
        mock_prompt_manager.register_template.assert_any_call(name='retrospect_phase', description='Template for the Retrospect phase of the EDRR cycle', template_text=RETROSPECT_PHASE_TEMPLATE, edrr_phase='RETROSPECT')

    @pytest.mark.medium
    def test_register_edrr_templates_error_handling_raises_error(self):
        """Test that errors are handled appropriately when registering templates.

ReqID: N/A"""
        mock_prompt_manager = MagicMock(spec=PromptManager)
        mock_prompt_manager.register_template.side_effect = ValueError('Template already registered')
        with patch('devsynth.application.edrr.templates.logger') as mock_logger:
            register_edrr_templates(mock_prompt_manager)
            mock_logger.warning.assert_called_once()
            assert 'Error registering EDRR templates' in mock_logger.warning.call_args[0][0]

    @pytest.mark.medium
    @pytest.mark.parametrize('phase,template', [(Phase.EXPAND, EXPAND_PHASE_TEMPLATE), (Phase.DIFFERENTIATE, DIFFERENTIATE_PHASE_TEMPLATE), (Phase.REFINE, REFINE_PHASE_TEMPLATE), (Phase.RETROSPECT, RETROSPECT_PHASE_TEMPLATE)])
    def test_template_for_each_phase_has_expected(self, phase, template):
        """Test that there is a template for each EDRR phase.

ReqID: N/A"""
        assert template is not None
        assert isinstance(template, str)
        assert len(template) > 0