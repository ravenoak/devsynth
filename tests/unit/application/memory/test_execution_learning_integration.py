"""
Unit tests for Execution Learning Integration.

This module tests the integration between execution trajectory learning,
pattern extraction, and semantic understanding enhancement.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from devsynth.application.memory.execution_learning_integration import ExecutionLearningIntegration
from devsynth.application.memory.execution_trajectory_collector import ExecutionTrace, ExecutionStep
from devsynth.application.memory.enhanced_knowledge_graph import EnhancedKnowledgeGraph
from devsynth.domain.models.memory import MemeticUnit, MemeticMetadata, MemeticSource, CognitiveType


class TestExecutionLearningIntegration:
    """Test execution learning integration functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.memory_manager = Mock()
        self.enhanced_graph = EnhancedKnowledgeGraph()
        self.integration = ExecutionLearningIntegration(self.memory_manager, self.enhanced_graph)

    def test_initialization(self):
        """Test integration initialization."""
        assert self.integration.memory_manager == self.memory_manager
        assert self.integration.enhanced_graph == self.enhanced_graph
        assert self.integration.max_trajectories == 1000
        assert len(self.integration.learning_history) == 0

    def test_learn_from_code_execution(self):
        """Test learning from code execution."""
        code_snippets = [
            "def add(a, b): return a + b",
            "def multiply(a, b): return a * b"
        ]

        # Mock the learning process
        with patch.object(self.integration.trajectory_collector, 'collect_python_trajectories') as mock_collect:
            mock_collect.return_value = [
                ExecutionTrace(
                    code=code_snippets[0],
                    execution_steps=[
                        ExecutionStep(
                            step_number=1,
                            line_number=1,
                            code_line="def add(a, b):"
                        )
                    ],
                    execution_outcome="success"
                )
            ]

            with patch.object(self.integration.learning_algorithm, 'train_on_trajectories') as mock_train:
                mock_train.return_value = {
                    "trajectories_processed": 1,
                    "patterns_extracted": 2,
                    "validation_score": 0.85,
                    "patterns": {"pattern1": Mock(), "pattern2": Mock()},
                    "understandings": {"understanding1": Mock()}
                }

                result = self.integration.learn_from_code_execution(code_snippets)

        assert result["success"] is True
        assert result["learning_session"]["code_snippets_count"] == 2
        assert result["validation_score"] == 0.85
        assert len(self.integration.learning_history) == 1

    def test_enhance_code_understanding(self):
        """Test code understanding enhancement."""
        code = "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)"

        # Mock pattern library
        with patch.object(self.integration.pattern_library, 'find_matches') as mock_find:
            mock_pattern = Mock()
            mock_pattern.pattern_id = "fib_pattern"
            mock_pattern.pattern_type = "recursive_algorithm"
            mock_pattern.confidence = 0.9
            mock_find.return_value = [mock_pattern]

            with patch.object(self.integration.understanding_engine, 'predict_execution_behavior') as mock_predict:
                mock_predict.return_value = {
                    "prediction": "recursive_execution",
                    "confidence": 0.85,
                    "predicted_success_rate": 0.9
                }

                with patch.object(self.integration.understanding_engine, 'analyze_behavioral_intent') as mock_intent:
                    mock_intent.return_value = Mock(
                        primary_purpose="fibonacci_calculation",
                        complexity_level="moderate",
                        intent_confidence=0.8
                    )

                    result = self.integration.enhance_code_understanding(code)

        assert "code_hash" in result
        assert "semantic_components" in result
        assert "behavioral_intent" in result
        assert "execution_prediction" in result
        assert "understanding_confidence" in result
        assert len(result["matching_patterns"]) == 1

    def test_semantic_robustness_testing(self):
        """Test semantic robustness with mutations."""
        original_code = "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)"
        mutated_code = "def fib_calc(num): return num if num <= 1 else fib_calc(num-1) + fib_calc(num-2)"

        # Mock understanding enhancement
        with patch.object(self.integration, 'enhance_code_understanding') as mock_enhance:
            mock_enhance.side_effect = [
                {
                    "understanding_confidence": 0.9,
                    "behavioral_intent": {"primary_purpose": "fibonacci_calculation"},
                    "semantic_components": {"semantic_fingerprint": "fib_hash_123"}
                },
                {
                    "understanding_confidence": 0.85,
                    "behavioral_intent": {"primary_purpose": "fibonacci_calculation"},
                    "semantic_components": {"semantic_fingerprint": "fib_hash_123"}
                }
            ]

            result = self.integration.test_semantic_robustness(original_code, mutated_code)

        assert "semantic_similarity" in result
        assert "understanding_preserved" in result
        assert result["understanding_preserved"] is True  # Should preserve understanding
        assert result["validation_method"] == "semantic_preservation_test"

    def test_get_learning_statistics(self):
        """Test learning statistics retrieval."""
        # Add mock learning session
        self.integration.learning_history = [
            {
                "timestamp": datetime.now(),
                "code_snippets_count": 5,
                "trajectories_collected": 5,
                "patterns_learned": 10,
                "understandings_built": 3,
                "validation_score": 0.8
            }
        ]

        # Mock pattern library
        with patch.object(self.integration.pattern_library, 'export_patterns') as mock_export:
            mock_export.return_value = {
                "patterns": {"pattern1": Mock()},
                "total_patterns": 1
            }

            stats = self.integration.get_learning_statistics()

        assert "learning_sessions" in stats
        assert stats["learning_sessions"] == 1
        assert "total_patterns_learned" in stats
        assert "pattern_library_size" in stats

    def test_validate_against_research_benchmarks(self):
        """Test validation against research benchmarks."""
        validation_suite = {
            "semantic_robustness": Mock(overall_score=0.91, benchmark_compliance={"mutation_resistance": True}),
            "execution_prediction": Mock(overall_score=0.83, benchmark_compliance={"prediction_accuracy": True}),
            "multi_hop_reasoning": Mock(overall_score=0.87, benchmark_compliance={"multi_hop_accuracy": True})
        }

        result = self.integration.validate_against_research_benchmarks(validation_suite)

        assert "research_benchmark_comparison" in result
        assert "research_alignment_score" in result
        assert result["research_alignment_score"] > 0.8  # Should meet research standards

    def test_export_import_learning_state(self):
        """Test learning state export and import."""
        # Set up learning state
        self.integration.learning_history = [{"test": "session"}]
        self.integration.understanding_cache = {"test": "cache"}

        # Mock pattern library export
        with patch.object(self.integration.pattern_library, 'export_patterns') as mock_export:
            mock_export.return_value = {"patterns": {}, "total_patterns": 0}

            # Export state
            exported_state = self.integration.export_learning_state()

        assert "learning_history" in exported_state
        assert "pattern_library" in exported_state
        assert "understanding_cache" in exported_state
        assert "export_timestamp" in exported_state

        # Import state
        with patch.object(self.integration.pattern_library, 'import_patterns') as mock_import:
            self.integration.import_learning_state(exported_state)

            mock_import.assert_called_once()

        assert len(self.integration.learning_history) == 1
        assert len(self.integration.understanding_cache) == 1


class TestExecutionTrajectoryCollector:
    """Test execution trajectory collection."""

    def setup_method(self):
        """Set up test fixtures."""
        self.collector = ExecutionTrajectoryCollector(sandbox_enabled=False)

    def test_initialization(self):
        """Test collector initialization."""
        assert self.collector.sandbox_enabled is False
        assert self.collector.max_execution_time == 30.0
        assert len(self.collector.execution_history) == 0

    def test_analyze_code_structure(self):
        """Test code structure analysis."""
        code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""

        # This would normally use AST parsing
        # For testing, verify the method exists and returns expected structure
        import ast
        tree = ast.parse(code)
        steps = self.collector._analyze_code_structure(tree)

        assert len(steps) > 0
        assert steps[0].step_number == 1
        assert "fibonacci" in steps[0].code_line

    def test_extract_execution_patterns(self):
        """Test execution pattern extraction."""
        traces = [
            ExecutionTrace(
                code="def add(a, b): return a + b",
                execution_steps=[
                    ExecutionStep(
                        step_number=1,
                        line_number=1,
                        code_line="def add(a, b):",
                        function_calls=["add"]
                    )
                ],
                execution_outcome="success"
            )
        ]

        patterns = self.collector.extract_execution_patterns(traces)

        assert "function_calls" in patterns
        assert "add" in patterns["function_calls"]
        assert patterns["function_calls"]["add"]["count"] == 1

    def test_create_memetic_units_from_trajectories(self):
        """Test Memetic Unit creation from trajectories."""
        traces = [
            ExecutionTrace(
                trace_id="test_trace_123",
                code="def test_function(): return 42",
                execution_outcome="42"
            )
        ]

        units = self.collector.create_memetic_units_from_trajectories(traces)

        assert len(units) > 0

        # Check episodic unit
        episodic_unit = next((u for u in units if u.metadata.cognitive_type == CognitiveType.EPISODIC), None)
        assert episodic_unit is not None
        assert episodic_unit.metadata.source == MemeticSource.CODE_EXECUTION

        # Check semantic unit
        semantic_unit = next((u for u in units if u.metadata.cognitive_type == CognitiveType.SEMANTIC), None)
        assert semantic_unit is not None
        assert "pattern" in semantic_unit.metadata.topic

    def test_get_execution_insights(self):
        """Test execution insights extraction."""
        traces = [
            ExecutionTrace(
                code="def fast_function(): return 1",
                execution_time=0.1,
                execution_outcome="1"
            ),
            ExecutionTrace(
                code="def slow_function(): import time; time.sleep(1); return 2",
                execution_time=1.0,
                execution_error="timeout"
            )
        ]

        insights = self.collector.get_execution_insights(traces)

        assert insights["total_traces"] == 2
        assert insights["successful_executions"] == 1
        assert insights["failed_executions"] == 1
        assert "performance_distribution" in insights
        assert "error_distribution" in insights

    def test_validate_trajectory_quality(self):
        """Test trajectory quality validation."""
        trace = ExecutionTrace(
            code="def complete_function(a, b): return a + b",
            execution_steps=[
                ExecutionStep(
                    step_number=1,
                    line_number=1,
                    code_line="def complete_function(a, b):"
                ),
                ExecutionStep(
                    step_number=2,
                    line_number=1,
                    code_line="return a + b"
                )
            ],
            execution_outcome="success",
            execution_time=0.05
        )

        quality = self.collector.validate_trajectory_quality(trace)

        assert quality["trace_id"] == str(trace.trace_id)
        assert quality["completeness_score"] > 0.5  # Should be reasonably complete
        assert quality["clarity_score"] > 0.5      # Should have clear outcome
        assert quality["usefulness_score"] > 0.5   # Should be useful
        assert quality["overall_quality"] > 0.6    # Overall should be good


class TestSemanticUnderstandingEngine:
    """Test semantic understanding engine."""

    def setup_method(self):
        """Set up test fixtures."""
        from devsynth.application.memory.semantic_understanding_engine import SemanticUnderstandingEngine
        from devsynth.application.memory.execution_learning_algorithm import PatternLibrary

        self.pattern_library = PatternLibrary()
        self.engine = SemanticUnderstandingEngine(self.pattern_library)

    def test_extract_semantic_components(self):
        """Test semantic component extraction."""
        code = """
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
"""

        components = self.engine.extract_semantic_components(code)

        assert components.structural_analysis is not None
        assert components.data_flow_patterns is not None
        assert components.behavioral_intentions is not None
        assert components.execution_mappings is not None
        assert components.semantic_fingerprint is not None and len(components.semantic_fingerprint) > 0

    def test_analyze_behavioral_intent(self):
        """Test behavioral intent analysis."""
        code = "def sort_numbers(numbers): return sorted(numbers)"

        intent = self.engine.analyze_behavioral_intent(code)

        assert intent.primary_purpose is not None
        assert len(intent.algorithmic_patterns) > 0
        assert intent.complexity_level in ["simple", "moderate", "complex", "very_complex"]
        assert 0.0 <= intent.intent_confidence <= 1.0

    def test_detect_semantic_equivalence(self):
        """Test semantic equivalence detection."""
        code1 = "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)"
        code2 = "def fib_calc(num): return num if num <= 1 else fib_calc(num-1) + fib_calc(num-2)"

        equivalence = self.engine.detect_semantic_equivalence(code1, code2)

        assert "is_equivalent" in equivalence
        assert "similarity_score" in equivalence
        assert "behavioral_match" in equivalence
        assert equivalence["validation_method"] == "multi_faceted_semantic_analysis"

    def test_predict_execution_behavior(self):
        """Test execution behavior prediction."""
        code = "def divide(a, b): return a / b"

        # Mock pattern library to return relevant patterns
        mock_pattern = Mock()
        mock_pattern.pattern_id = "division_pattern"
        mock_pattern.pattern_type = "mathematical_operation"
        mock_pattern.confidence = 0.8
        mock_pattern.expected_outcomes = {"success_rate": 0.7}

        with patch.object(self.engine.pattern_library, 'find_matches') as mock_find:
            mock_find.return_value = [mock_pattern]

            prediction = self.engine.predict_execution_behavior(code)

        assert "prediction" in prediction
        assert "confidence" in prediction
        assert "supporting_patterns" in prediction
        assert prediction["confidence"] >= 0.0
