"""
Unit tests for the prompt auto-tuning module.
"""
import pytest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock

from devsynth.application.prompts.auto_tuning import PromptVariant, PromptAutoTuner, PromptAutoTuningError


class TestPromptVariant:
    """Tests for the PromptVariant class."""
    
    def test_initialization(self):
        """Test initialization of a PromptVariant."""
        template = "This is a test template."
        variant = PromptVariant(template)
        
        assert variant.template == template
        assert variant.variant_id is not None
        assert variant.usage_count == 0
        assert variant.success_count == 0
        assert variant.failure_count == 0
        assert variant.feedback_scores == []
        assert variant.last_used is None
    
    def test_success_rate(self):
        """Test success rate calculation."""
        variant = PromptVariant("Test template")
        
        # No usage yet
        assert variant.success_rate == 0.0
        
        # Record some usage
        variant.record_usage(success=True)
        assert variant.success_rate == 1.0
        
        variant.record_usage(success=False)
        assert variant.success_rate == 0.5
        
        variant.record_usage(success=True)
        assert variant.success_rate == 2/3
    
    def test_average_feedback_score(self):
        """Test average feedback score calculation."""
        variant = PromptVariant("Test template")
        
        # No feedback yet
        assert variant.average_feedback_score == 0.0
        
        # Record some feedback
        variant.record_usage(feedback_score=0.8)
        assert variant.average_feedback_score == 0.8
        
        variant.record_usage(feedback_score=0.6)
        assert variant.average_feedback_score == 0.7
    
    def test_performance_score(self):
        """Test performance score calculation."""
        variant = PromptVariant("Test template")
        
        # No usage yet
        assert variant.performance_score == 0.0
        
        # Record some usage with success and feedback
        variant.record_usage(success=True, feedback_score=0.8)
        
        # Performance score should be weighted combination of success rate and feedback
        expected_score = (0.7 * 1.0) + (0.3 * 0.8)
        assert variant.performance_score == pytest.approx(expected_score)
    
    def test_record_usage(self):
        """Test recording usage."""
        variant = PromptVariant("Test template")
        
        # Record usage without success or feedback
        variant.record_usage()
        assert variant.usage_count == 1
        assert variant.last_used is not None
        assert variant.success_count == 0
        assert variant.failure_count == 0
        assert variant.feedback_scores == []
        
        # Record successful usage with feedback
        variant.record_usage(success=True, feedback_score=0.9)
        assert variant.usage_count == 2
        assert variant.success_count == 1
        assert variant.failure_count == 0
        assert variant.feedback_scores == [0.9]
        
        # Record failed usage with feedback
        variant.record_usage(success=False, feedback_score=0.3)
        assert variant.usage_count == 3
        assert variant.success_count == 1
        assert variant.failure_count == 1
        assert variant.feedback_scores == [0.9, 0.3]
    
    def test_to_dict_and_from_dict(self):
        """Test conversion to and from dictionary."""
        template = "Test template"
        variant = PromptVariant(template, "test-id")
        variant.record_usage(success=True, feedback_score=0.8)
        
        # Convert to dictionary
        data = variant.to_dict()
        
        # Check dictionary contents
        assert data["variant_id"] == "test-id"
        assert data["template"] == template
        assert data["usage_count"] == 1
        assert data["success_count"] == 1
        assert data["failure_count"] == 0
        assert data["feedback_scores"] == [0.8]
        assert data["last_used"] is not None
        
        # Convert back to PromptVariant
        new_variant = PromptVariant.from_dict(data)
        
        # Check that the new variant matches the original
        assert new_variant.variant_id == variant.variant_id
        assert new_variant.template == variant.template
        assert new_variant.usage_count == variant.usage_count
        assert new_variant.success_count == variant.success_count
        assert new_variant.failure_count == variant.failure_count
        assert new_variant.feedback_scores == variant.feedback_scores
        assert new_variant.last_used == variant.last_used


class TestPromptAutoTuner:
    """Tests for the PromptAutoTuner class."""
    
    @pytest.fixture
    def auto_tuner(self):
        """Create a PromptAutoTuner instance for testing."""
        return PromptAutoTuner()
    
    def test_initialization(self, auto_tuner):
        """Test initialization of a PromptAutoTuner."""
        assert auto_tuner.prompt_variants == {}
        assert auto_tuner.selection_strategy == "performance"
        assert auto_tuner.exploration_rate == 0.2
    
    def test_register_template(self, auto_tuner):
        """Test registering a prompt template."""
        template_id = "test-template"
        template = "This is a test template."
        
        auto_tuner.register_template(template_id, template)
        
        assert template_id in auto_tuner.prompt_variants
        assert len(auto_tuner.prompt_variants[template_id]) == 1
        assert auto_tuner.prompt_variants[template_id][0].template == template
    
    def test_select_variant_single(self, auto_tuner):
        """Test selecting a variant when there's only one."""
        template_id = "test-template"
        template = "This is a test template."
        
        auto_tuner.register_template(template_id, template)
        variant = auto_tuner.select_variant(template_id)
        
        assert variant.template == template
        assert variant.usage_count == 1  # Should record usage
    
    def test_select_variant_error(self, auto_tuner):
        """Test selecting a variant for an unregistered template."""
        with pytest.raises(PromptAutoTuningError):
            auto_tuner.select_variant("nonexistent-template")
    
    def test_select_variant_performance(self, auto_tuner):
        """Test selecting a variant based on performance."""
        template_id = "test-template"
        
        # Register template and create multiple variants
        auto_tuner.register_template(template_id, "Variant 1")
        auto_tuner.prompt_variants[template_id].append(PromptVariant("Variant 2"))
        auto_tuner.prompt_variants[template_id].append(PromptVariant("Variant 3"))
        
        # Make variant 2 the best performer
        auto_tuner.prompt_variants[template_id][1].record_usage(success=True, feedback_score=1.0)
        
        # Set exploration rate to 0 to always select best performer
        auto_tuner.exploration_rate = 0.0
        
        # Select variant
        variant = auto_tuner.select_variant(template_id)
        
        # Should select variant 2 (the best performer)
        assert variant.template == "Variant 2"
    
    def test_record_feedback(self, auto_tuner):
        """Test recording feedback for a variant."""
        template_id = "test-template"
        
        # Register template
        auto_tuner.register_template(template_id, "Test template")
        variant = auto_tuner.prompt_variants[template_id][0]
        
        # Record feedback
        auto_tuner.record_feedback(template_id, variant.variant_id, success=True, feedback_score=0.9)
        
        # Check that feedback was recorded
        assert variant.success_count == 1
        assert variant.feedback_scores == [0.9]
    
    def test_record_feedback_error(self, auto_tuner):
        """Test recording feedback for an unregistered template or variant."""
        with pytest.raises(PromptAutoTuningError):
            auto_tuner.record_feedback("nonexistent-template", "nonexistent-variant")
        
        # Register template but use nonexistent variant
        auto_tuner.register_template("test-template", "Test template")
        with pytest.raises(PromptAutoTuningError):
            auto_tuner.record_feedback("test-template", "nonexistent-variant")
    
    @patch('devsynth.application.prompts.auto_tuning.PromptAutoTuner._mutate_variant')
    def test_generate_variants(self, mock_mutate, auto_tuner):
        """Test generating new variants."""
        template_id = "test-template"
        
        # Register template
        auto_tuner.register_template(template_id, "Test template")
        variant = auto_tuner.prompt_variants[template_id][0]
        
        # Mock the mutate method to return a specific variant
        new_variant = PromptVariant("Mutated template")
        mock_mutate.return_value = new_variant
        
        # Record enough usage to trigger variant generation
        for _ in range(5):
            variant.record_usage(success=True)
        
        # Trigger variant generation
        auto_tuner._generate_variants_if_needed(template_id)
        
        # Check that a new variant was generated
        assert len(auto_tuner.prompt_variants[template_id]) == 2
        assert auto_tuner.prompt_variants[template_id][1] == new_variant
    
    def test_mutation_methods(self, auto_tuner):
        """Test the mutation methods."""
        template = "This is a test template.\n\nIt has multiple sections.\n\nPlease use it carefully."
        
        # Test add_detail
        mutated = auto_tuner._add_detail(template)
        assert len(mutated.split("\n")) > len(template.split("\n"))
        
        # Test change_tone
        mutated = auto_tuner._change_tone(template)
        assert mutated != template
        
        # Test reorder_sections
        mutated = auto_tuner._reorder_sections(template)
        assert mutated.startswith("This is a test template.")  # First section should stay in place
        
        # Test adjust_emphasis
        mutated = auto_tuner._adjust_emphasis(template)
        assert mutated != template or "**" in mutated or "_" in mutated or any(word.isupper() for word in mutated.split())
    
    def test_storage(self):
        """Test loading and saving variants to storage."""
        # Create a temporary directory for storage
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create an auto-tuner with storage
            auto_tuner = PromptAutoTuner(storage_path=temp_dir)
            
            # Register a template and record some usage
            auto_tuner.register_template("test-template", "Test template")
            variant = auto_tuner.prompt_variants["test-template"][0]
            auto_tuner.record_feedback("test-template", variant.variant_id, success=True, feedback_score=0.9)
            
            # Check that the storage file was created
            storage_file = os.path.join(temp_dir, "prompt_variants.json")
            assert os.path.exists(storage_file)
            
            # Load the storage file and check its contents
            with open(storage_file, "r") as f:
                data = json.load(f)
            
            assert "test-template" in data
            assert len(data["test-template"]) == 1
            assert data["test-template"][0]["template"] == "Test template"
            assert data["test-template"][0]["success_count"] == 1
            assert data["test-template"][0]["feedback_scores"] == [0.9]
            
            # Create a new auto-tuner that should load from storage
            new_auto_tuner = PromptAutoTuner(storage_path=temp_dir)
            
            # Check that the variants were loaded
            assert "test-template" in new_auto_tuner.prompt_variants
            assert len(new_auto_tuner.prompt_variants["test-template"]) == 1
            assert new_auto_tuner.prompt_variants["test-template"][0].template == "Test template"
            assert new_auto_tuner.prompt_variants["test-template"][0].success_count == 1
            assert new_auto_tuner.prompt_variants["test-template"][0].feedback_scores == [0.9]