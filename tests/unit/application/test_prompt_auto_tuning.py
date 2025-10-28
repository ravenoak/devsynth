"""
Unit tests for the prompt auto-tuning module.
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.prompts.auto_tuning import (
    PromptAutoTuner,
    PromptAutoTuningError,
    PromptVariant,
)


class TestPromptVariant:
    """Tests for the PromptVariant class.

    ReqID: FR-56"""

    @pytest.mark.medium
    def test_initialization_succeeds(self):
        """Test initialization of a PromptVariant.

        ReqID: FR-56"""
        template = "This is a test template."
        variant = PromptVariant(template)
        assert variant.template == template
        assert variant.variant_id is not None
        assert variant.usage_count == 0
        assert variant.success_count == 0
        assert variant.failure_count == 0
        assert variant.feedback_scores == []
        assert variant.last_used is None

    @pytest.mark.medium
    def test_success_rate_succeeds(self):
        """Test success rate calculation.

        ReqID: FR-56"""
        variant = PromptVariant("Test template")
        assert variant.success_rate == 0.0
        variant.record_usage(success=True)
        assert variant.success_rate == 1.0
        variant.record_usage(success=False)
        assert variant.success_rate == 0.5
        variant.record_usage(success=True)
        assert variant.success_rate == 2 / 3

    @pytest.mark.medium
    def test_average_feedback_score_succeeds(self):
        """Test average feedback score calculation.

        ReqID: FR-56"""
        variant = PromptVariant("Test template")
        assert variant.average_feedback_score == 0.0
        variant.record_usage(feedback_score=0.8)
        assert variant.average_feedback_score == 0.8
        variant.record_usage(feedback_score=0.6)
        assert variant.average_feedback_score == 0.7

    @pytest.mark.medium
    def test_performance_score_succeeds(self):
        """Test performance score calculation.

        ReqID: FR-56"""
        variant = PromptVariant("Test template")
        assert variant.performance_score == 0.0
        variant.record_usage(success=True, feedback_score=0.8)
        expected_score = 0.7 * 1.0 + 0.3 * 0.8
        assert variant.performance_score == pytest.approx(expected_score)

    @pytest.mark.medium
    def test_record_usage_succeeds(self):
        """Test recording usage.

        ReqID: FR-56"""
        variant = PromptVariant("Test template")
        variant.record_usage()
        assert variant.usage_count == 1
        assert variant.last_used is not None
        assert variant.success_count == 0
        assert variant.failure_count == 0
        assert variant.feedback_scores == []
        variant.record_usage(success=True, feedback_score=0.9)
        assert variant.usage_count == 2
        assert variant.success_count == 1
        assert variant.failure_count == 0
        assert variant.feedback_scores == [0.9]
        variant.record_usage(success=False, feedback_score=0.3)
        assert variant.usage_count == 3
        assert variant.success_count == 1
        assert variant.failure_count == 1
        assert variant.feedback_scores == [0.9, 0.3]

    @pytest.mark.medium
    def test_to_dict_and_from_dict_succeeds(self):
        """Test conversion to and from dictionary.

        ReqID: FR-56"""
        template = "Test template"
        variant = PromptVariant(template, "test-id")
        variant.record_usage(success=True, feedback_score=0.8)
        data = variant.to_dict()
        assert data["variant_id"] == "test-id"
        assert data["template"] == template
        assert data["usage_count"] == 1
        assert data["success_count"] == 1
        assert data["failure_count"] == 0
        assert data["feedback_scores"] == [0.8]
        assert data["last_used"] is not None
        new_variant = PromptVariant.from_dict(data)
        assert new_variant.variant_id == variant.variant_id
        assert new_variant.template == variant.template
        assert new_variant.usage_count == variant.usage_count
        assert new_variant.success_count == variant.success_count
        assert new_variant.failure_count == variant.failure_count
        assert new_variant.feedback_scores == variant.feedback_scores
        assert new_variant.last_used == variant.last_used


class TestPromptAutoTuner:
    """Tests for the PromptAutoTuner class.

    ReqID: FR-56"""

    @pytest.fixture
    def auto_tuner(self):
        """Create a PromptAutoTuner instance for testing."""
        return PromptAutoTuner()

    @pytest.mark.medium
    def test_auto_tuner_initialization_succeeds(self, auto_tuner):
        """Test initialization of a PromptAutoTuner.

        ReqID: FR-56"""
        assert auto_tuner.prompt_variants == {}
        assert auto_tuner.selection_strategy == "performance"
        assert auto_tuner.exploration_rate == 0.2

    @pytest.mark.medium
    def test_register_template_succeeds(self, auto_tuner):
        """Test registering a prompt template.

        ReqID: FR-56"""
        template_id = "test-template"
        template = "This is a test template."
        auto_tuner.register_template(template_id, template)
        assert template_id in auto_tuner.prompt_variants
        assert len(auto_tuner.prompt_variants[template_id]) == 1
        assert auto_tuner.prompt_variants[template_id][0].template == template

    @pytest.mark.medium
    def test_select_variant_single_succeeds(self, auto_tuner):
        """Test selecting a variant when there's only one.

        ReqID: FR-56"""
        template_id = "test-template"
        template = "This is a test template."
        auto_tuner.register_template(template_id, template)
        variant = auto_tuner.select_variant(template_id)
        assert variant.template == template
        assert variant.usage_count == 1

    @pytest.mark.medium
    def test_select_variant_error_succeeds(self, auto_tuner):
        """Test selecting a variant for an unregistered template.

        ReqID: FR-56"""
        with pytest.raises(PromptAutoTuningError):
            auto_tuner.select_variant("nonexistent-template")

    @pytest.mark.medium
    def test_select_variant_performance_succeeds(self, auto_tuner):
        """Test selecting a variant based on performance.

        ReqID: FR-56"""
        template_id = "test-template"
        auto_tuner.register_template(template_id, "Variant 1")
        auto_tuner.prompt_variants[template_id].append(PromptVariant("Variant 2"))
        auto_tuner.prompt_variants[template_id].append(PromptVariant("Variant 3"))
        auto_tuner.prompt_variants[template_id][1].record_usage(
            success=True, feedback_score=1.0
        )
        auto_tuner.exploration_rate = 0.0
        variant = auto_tuner.select_variant(template_id)
        assert variant.template == "Variant 2"

    @pytest.mark.medium
    def test_record_feedback_succeeds(self, auto_tuner):
        """Test recording feedback for a variant.

        ReqID: FR-56"""
        template_id = "test-template"
        auto_tuner.register_template(template_id, "Test template")
        variant = auto_tuner.prompt_variants[template_id][0]
        auto_tuner.record_feedback(
            template_id, variant.variant_id, success=True, feedback_score=0.9
        )
        assert variant.success_count == 1
        assert variant.feedback_scores == [0.9]

    @pytest.mark.medium
    def test_record_feedback_error_succeeds(self, auto_tuner):
        """Test recording feedback for an unregistered template or variant.

        ReqID: FR-56"""
        with pytest.raises(PromptAutoTuningError):
            auto_tuner.record_feedback("nonexistent-template", "nonexistent-variant")
        auto_tuner.register_template("test-template", "Test template")
        with pytest.raises(PromptAutoTuningError):
            auto_tuner.record_feedback("test-template", "nonexistent-variant")

    @patch("devsynth.application.prompts.auto_tuning.PromptAutoTuner._mutate_variant")
    @pytest.mark.medium
    def test_generate_variants_succeeds(self, mock_mutate, auto_tuner):
        """Test generating new variants.

        ReqID: FR-56"""
        template_id = "test-template"
        auto_tuner.register_template(template_id, "Test template")
        variant = auto_tuner.prompt_variants[template_id][0]
        new_variant = PromptVariant("Mutated template")
        mock_mutate.return_value = new_variant
        for _ in range(5):
            variant.record_usage(success=True)
        auto_tuner._generate_variants_if_needed(template_id)
        assert len(auto_tuner.prompt_variants[template_id]) == 2
        assert auto_tuner.prompt_variants[template_id][1] == new_variant

    @pytest.mark.medium
    def test_mutation_methods_succeeds(self, auto_tuner):
        """Test the mutation methods.

        ReqID: FR-56"""
        template = "This is a test template.\n\nIt has multiple sections.\n\nPlease use it carefully."
        mutated = auto_tuner._add_detail(template)
        assert len(mutated.split("\n")) > len(template.split("\n"))
        mutated = auto_tuner._change_tone(template)
        assert mutated != template
        mutated = auto_tuner._reorder_sections(template)
        assert mutated.startswith("This is a test template.")
        mutated = auto_tuner._adjust_emphasis(template)
        assert (
            mutated != template
            or "**" in mutated
            or "_" in mutated
            or any(word.isupper() for word in mutated.split())
        )

    @pytest.mark.medium
    def test_storage_succeeds(self):
        """Test loading and saving variants to storage.

        ReqID: FR-56"""
        with tempfile.TemporaryDirectory() as temp_dir:
            auto_tuner = PromptAutoTuner(storage_path=temp_dir)
            auto_tuner.register_template("test-template", "Test template")
            variant = auto_tuner.prompt_variants["test-template"][0]
            auto_tuner.record_feedback(
                "test-template", variant.variant_id, success=True, feedback_score=0.9
            )
            storage_file = os.path.join(temp_dir, "prompt_variants.json")
            assert os.path.exists(storage_file)
            with open(storage_file) as f:
                data = json.load(f)
            assert "test-template" in data
            assert len(data["test-template"]) == 1
            assert data["test-template"][0]["template"] == "Test template"
            assert data["test-template"][0]["success_count"] == 1
            assert data["test-template"][0]["feedback_scores"] == [0.9]
            new_auto_tuner = PromptAutoTuner(storage_path=temp_dir)
            assert "test-template" in new_auto_tuner.prompt_variants
            assert len(new_auto_tuner.prompt_variants["test-template"]) == 1
            assert (
                new_auto_tuner.prompt_variants["test-template"][0].template
                == "Test template"
            )
            assert new_auto_tuner.prompt_variants["test-template"][0].success_count == 1
            assert new_auto_tuner.prompt_variants["test-template"][
                0
            ].feedback_scores == [0.9]
