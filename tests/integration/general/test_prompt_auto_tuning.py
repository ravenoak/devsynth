import pytest

import os
from devsynth.application.prompts.prompt_manager import PromptManager


def test_auto_tuner_disabled_by_default_succeeds(tmp_path):
    """Test that auto tuner disabled by default succeeds.

ReqID: N/A"""
    storage = tmp_path / 'prompts'
    pm = PromptManager(storage_path=str(storage))
    assert pm.auto_tuner is None


@pytest.mark.medium
def test_prompt_auto_tuning_feedback_loop_succeeds(tmp_path):
    """Test that prompt auto tuning feedback loop succeeds.

ReqID: N/A"""
    storage = tmp_path / 'prompts'
    pm = PromptManager(storage_path=str(storage), config={'features': {
        'prompt_auto_tuning': True}})
    assert pm.auto_tuner is not None
    pm.auto_tuner.exploration_rate = 0.0
    pm.register_template('greet', 'Greeting template', 'Hello {name}')
    for i in range(6):
        rendered = pm.render_prompt('greet', {'name': f'User{i}'})
        assert f'User{i}' in rendered
        success = i % 2 == 0
        score = 0.9 if success else 0.1
        pm.record_tuning_feedback('greet', success=success, feedback_score=
            score)
    variants = pm.auto_tuner.prompt_variants['greet']
    assert variants[0].usage_count >= 6
    assert os.path.exists(storage / 'prompt_variants.json')
