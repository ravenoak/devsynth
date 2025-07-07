"""
Unit tests for the enhanced recursion features in the EDRR Framework.

This module tests the enhanced termination conditions, result aggregation,
and recursion effectiveness metrics in the EDRRCoordinator.
"""

import copy
import json
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.edrr.coordinator import EDRRCoordinator
from devsynth.methodology.base import Phase


@pytest.fixture
def mock_dependencies():
    """Create mock dependencies for the EDRRCoordinator."""
    memory_manager = MagicMock()
    wsde_team = MagicMock()
    code_analyzer = MagicMock()
    ast_transformer = MagicMock()
    prompt_manager = MagicMock()
    documentation_manager = MagicMock()

    return {
        "memory_manager": memory_manager,
        "wsde_team": wsde_team,
        "code_analyzer": code_analyzer,
        "ast_transformer": ast_transformer,
        "prompt_manager": prompt_manager,
        "documentation_manager": documentation_manager,
    }


@pytest.fixture
def coordinator(mock_dependencies):
    """Create an EDRRCoordinator instance for testing."""
    coordinator = EDRRCoordinator(
        memory_manager=mock_dependencies["memory_manager"],
        wsde_team=mock_dependencies["wsde_team"],
        code_analyzer=mock_dependencies["code_analyzer"],
        ast_transformer=mock_dependencies["ast_transformer"],
        prompt_manager=mock_dependencies["prompt_manager"],
        documentation_manager=mock_dependencies["documentation_manager"],
        enable_enhanced_logging=True,
    )

    # Set up a basic configuration
    coordinator.config = {
        "edrr": {
            "recursion": {
                "thresholds": {
                    "granularity": 0.25,
                    "cost_benefit": 0.6,
                    "quality": 0.85,
                    "resource": 0.75,
                    "complexity": 0.8,
                    "convergence": 0.9,
                    "diminishing_returns": 0.2,
                }
            },
            "aggregation": {
                "merge_similar": True,
                "prioritize_by_quality": True,
                "handle_conflicts": True,
            }
        }
    }

    return coordinator


class TestTerminationConditions:
    """Test the enhanced termination conditions for recursive EDRR cycles."""

    def test_human_override_terminate(self, coordinator):
        """Test that human override to terminate works."""
        task = {"human_override": "terminate"}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is True
        assert reason == "human override"

    def test_human_override_continue(self, coordinator):
        """Test that human override to continue works."""
        task = {"human_override": "continue"}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is False
        assert reason is None

    def test_granularity_threshold(self, coordinator):
        """Test that granularity threshold works."""
        # Below threshold, should terminate
        task = {"granularity_score": 0.2}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is True
        assert reason == "granularity threshold"

        # Above threshold, should continue
        task = {"granularity_score": 0.3}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is False
        assert reason is None

    def test_cost_benefit_analysis(self, coordinator):
        """Test that cost-benefit analysis works."""
        # Above threshold, should terminate
        task = {"cost_score": 0.7, "benefit_score": 0.5}  # Ratio: 1.4
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is True
        assert reason == "cost-benefit analysis"

        # Below threshold, should continue
        task = {"cost_score": 0.3, "benefit_score": 0.5}  # Ratio: 0.6
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is False
        assert reason is None

        # Zero benefit, should terminate
        task = {"cost_score": 0.5, "benefit_score": 0}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is True
        assert reason == "cost-benefit analysis"

    def test_quality_threshold(self, coordinator):
        """Test that quality threshold works."""
        # Above threshold, should terminate
        task = {"quality_score": 0.9}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is True
        assert reason == "quality threshold"

        # Below threshold, should continue
        task = {"quality_score": 0.8}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is False
        assert reason is None

    def test_resource_limit(self, coordinator):
        """Test that resource limit works."""
        # Above threshold, should terminate
        task = {"resource_usage": 0.8}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is True
        assert reason == "resource limit"

        # Below threshold, should continue
        task = {"resource_usage": 0.7}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is False
        assert reason is None

    def test_complexity_threshold(self, coordinator):
        """Test that complexity threshold works."""
        # Above threshold, should terminate
        task = {"complexity_score": 0.85}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is True
        assert reason == "complexity threshold"

        # Below threshold, should continue
        task = {"complexity_score": 0.75}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is False
        assert reason is None

    def test_convergence_threshold(self, coordinator):
        """Test that convergence threshold works."""
        # Above threshold, should terminate
        task = {"convergence_score": 0.95}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is True
        assert reason == "convergence threshold"

        # Below threshold, should continue
        task = {"convergence_score": 0.85}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is False
        assert reason is None

    def test_diminishing_returns(self, coordinator):
        """Test that diminishing returns threshold works."""
        # Below threshold, should terminate
        task = {"improvement_rate": 0.15}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is True
        assert reason == "diminishing returns"

        # Above threshold, should continue
        task = {"improvement_rate": 0.25}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is False
        assert reason is None

    def test_parent_phase_compatibility(self, coordinator):
        """Test that parent phase compatibility works."""
        # Set up a coordinator with parent phase RETROSPECT and recursion depth 1
        coordinator.parent_phase = Phase.RETROSPECT
        coordinator.recursion_depth = 1

        # Should terminate due to parent phase compatibility
        task = {}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is True
        assert reason == "parent phase compatibility"

        # Change parent phase to EXPAND, should continue
        coordinator.parent_phase = Phase.EXPAND
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is False
        assert reason is None

    def test_historical_effectiveness(self, coordinator, mock_dependencies):
        """Test that historical effectiveness check works."""
        # Set up memory manager to return patterns indicating ineffectiveness
        patterns = [
            {"task_type": "test", "recursion_effectiveness": 0.3}
        ]
        mock_dependencies["memory_manager"].retrieve_historical_patterns.return_value = patterns

        # Should terminate due to historical ineffectiveness
        task = {"type": "test"}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is True
        assert reason == "historical ineffectiveness"

        # Change task type, should continue
        task = {"type": "other"}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is False
        assert reason is None


class TestResultAggregation:
    """Test the enhanced result aggregation from micro cycles."""

    def test_process_phase_results_merge_similar(self, coordinator):
        """Test that similar results are merged in phase results."""
        # Create phase results with similar micro cycle results
        phase_results = {
            "micro_cycle_results": {
                "cycle1": {
                    "type": "analysis",
                    "description": "Analysis of code",
                    "findings": ["Issue 1", "Issue 2"]
                },
                "cycle2": {
                    "type": "analysis",
                    "description": "Analysis of code",
                    "findings": ["Issue 2", "Issue 3"]
                }
            }
        }

        # Process the phase results
        processed = coordinator._process_phase_results(phase_results, Phase.EXPAND)

        # Check that similar results were merged
        assert "micro_cycle_results" in processed
        assert len(processed["micro_cycle_results"]) == 1

        # Get the merged result
        merged_key = next(iter(processed["micro_cycle_results"]))
        merged = processed["micro_cycle_results"][merged_key]

        # Check that the merged result contains data from both cycles
        assert "merged_from" in merged
        assert "cycle1" in merged["merged_from"]
        assert "cycle2" in merged["merged_from"]
        assert set(merged["findings"]) == {"Issue 1", "Issue 2", "Issue 3"}

    def test_process_phase_results_prioritize_by_quality(self, coordinator):
        """Test that results are prioritized by quality in phase results."""
        # Create phase results with different quality scores
        phase_results = {
            "micro_cycle_results": {
                "cycle1": {
                    "type": "analysis",
                    "description": "Low quality analysis",
                    "quality_score": 0.3
                },
                "cycle2": {
                    "type": "analysis",
                    "description": "High quality analysis",
                    "quality_score": 0.8
                }
            }
        }

        # Process the phase results
        processed = coordinator._process_phase_results(phase_results, Phase.EXPAND)

        # Check that results were prioritized by quality
        assert "top_results" in processed
        assert len(processed["top_results"]) == 2

        # The first result should be the high quality one
        top_key = next(iter(processed["top_results"]))
        assert processed["top_results"][top_key]["quality_score"] == 0.8

    def test_process_phase_results_handle_conflicts(self, coordinator):
        """Test that conflicts are handled in phase results."""
        # Create phase results with conflicting approaches
        phase_results = {
            "micro_cycle_results": {
                "cycle1": {
                    "type": "implementation",
                    "approach": "Use a database",
                    "quality_score": 0.7
                },
                "cycle2": {
                    "type": "implementation",
                    "approach": "Use a file system",
                    "quality_score": 0.6
                }
            }
        }

        # Process the phase results
        processed = coordinator._process_phase_results(phase_results, Phase.REFINE)

        # Check that conflicts were identified and resolved
        assert "resolved_conflicts" in processed
        assert "approach" in processed["resolved_conflicts"]

        # The primary approach should be the higher quality one
        resolved = processed["resolved_conflicts"]["approach"]
        assert resolved["primary_approach"]["quality_score"] == 0.7
        assert len(resolved["alternative_approaches"]) == 1

    def test_merge_cycle_results(self, coordinator):
        """Test merging results from multiple cycles."""
        # Create mock cycles with results
        cycle1 = MagicMock()
        cycle1.cycle_id = "cycle1"
        cycle1.results = {
            "EXPAND": {
                "ideas": ["Idea 1", "Idea 2"]
            }
        }

        cycle2 = MagicMock()
        cycle2.cycle_id = "cycle2"
        cycle2.results = {
            "EXPAND": {
                "ideas": ["Idea 2", "Idea 3"]
            }
        }

        # Merge the cycle results
        merged = coordinator._merge_cycle_results([cycle1, cycle2])

        # Check that the results were merged
        assert len(merged) == 1

        # Get the merged result
        merged_key = next(iter(merged))
        merged_result = merged[merged_key]

        # Check that the merged result contains data from both cycles
        assert "merged_from" in merged_result
        assert "cycle1" in merged_result["merged_from"]
        assert "cycle2" in merged_result["merged_from"]
        assert "ideas" in merged_result
        assert set(merged_result["ideas"]) == {"Idea 1", "Idea 2", "Idea 3"}

    def test_calculate_similarity_key(self, coordinator):
        """Test calculating similarity keys for results."""
        # Test with a dictionary
        result1 = {
            "type": "analysis",
            "description": "Analysis of code",
            "findings": ["Issue 1", "Issue 2"]
        }
        key1 = coordinator._calculate_similarity_key(result1)

        # Test with a similar dictionary
        result2 = {
            "type": "analysis",
            "description": "Analysis of code",
            "findings": ["Issue 2", "Issue 3"]
        }
        key2 = coordinator._calculate_similarity_key(result2)

        # Test with a different dictionary
        result3 = {
            "type": "implementation",
            "description": "Implementation of feature",
            "code": "def foo(): pass"
        }
        key3 = coordinator._calculate_similarity_key(result3)

        # Similar dictionaries should have the same key
        assert key1 == key2
        # Different dictionaries should have different keys
        assert key1 != key3

    def test_merge_similar_results(self, coordinator):
        """Test merging similar results."""
        # Create similar results
        result1 = {
            "type": "analysis",
            "description": "Analysis of code",
            "findings": ["Issue 1", "Issue 2"]
        }
        result2 = {
            "type": "analysis",
            "description": "Analysis of code",
            "findings": ["Issue 2", "Issue 3"]
        }

        # Merge the results
        merged = coordinator._merge_similar_results([("cycle1", result1), ("cycle2", result2)])

        # Check that the merged result contains data from both results
        assert "merged_from" in merged
        assert "cycle1" in merged["merged_from"]
        assert "cycle2" in merged["merged_from"]
        assert "findings" in merged
        assert set(merged["findings"]) == {"Issue 1", "Issue 2", "Issue 3"}

    def test_merge_dicts(self, coordinator):
        """Test merging dictionaries."""
        # Create dictionaries to merge
        dict1 = {
            "key1": "value1",
            "key2": ["item1", "item2"],
            "key3": {"subkey1": "subvalue1"}
        }
        dict2 = {
            "key2": ["item2", "item3"],
            "key3": {"subkey2": "subvalue2"},
            "key4": "value4"
        }

        # Merge the dictionaries
        merged = coordinator._merge_dicts(dict1, dict2)

        # Check that the merged dictionary contains data from both dictionaries
        assert merged["key1"] == "value1"
        assert set(merged["key2"]) == {"item1", "item2", "item3"}
        assert merged["key3"]["subkey1"] == "subvalue1"
        assert merged["key3"]["subkey2"] == "subvalue2"
        assert merged["key4"] == "value4"

    def test_merge_lists(self, coordinator):
        """Test merging lists."""
        # Create lists to merge
        list1 = ["item1", "item2", "item3"]
        list2 = ["item2", "item3", "item4"]

        # Merge the lists
        merged = coordinator._merge_lists(list1, list2)

        # Check that the merged list contains items from both lists without duplicates
        assert set(merged) == {"item1", "item2", "item3", "item4"}

    def test_are_items_similar(self, coordinator):
        """Test checking if items are similar."""
        # Test with similar dictionaries
        item1 = {
            "id": "1",
            "type": "analysis",
            "description": "Analysis of code",
            "extra": "value1"
        }
        item2 = {
            "id": "1",
            "type": "analysis",
            "description": "Analysis of code",
            "extra": "value2"
        }
        assert coordinator._are_items_similar(item1, item2) is True

        # Test with different dictionaries
        item3 = {
            "id": "2",
            "type": "implementation",
            "description": "Implementation of feature",
            "extra": "value3"
        }
        assert coordinator._are_items_similar(item1, item3) is False

        # Test with non-dictionaries
        assert coordinator._are_items_similar("string1", "string1") is True
        assert coordinator._are_items_similar("string1", "string2") is False

    def test_calculate_quality_score(self, coordinator):
        """Test calculating quality scores for results."""
        # Test with a high quality result
        result1 = {
            "description": "High quality analysis",
            "approach": "Sophisticated approach",
            "implementation": "Detailed implementation",
            "analysis": "Thorough analysis",
            "solution": "Elegant solution"
        }
        score1 = coordinator._calculate_quality_score(result1)

        # Test with a low quality result
        result2 = {
            "description": "Low quality analysis"
        }
        score2 = coordinator._calculate_quality_score(result2)

        # Test with an explicit quality score
        result3 = {
            "description": "Medium quality analysis",
            "quality_score": 0.6
        }
        score3 = coordinator._calculate_quality_score(result3)

        # Test with an error
        result4 = {
            "description": "Failed analysis",
            "error": "Something went wrong"
        }
        score4 = coordinator._calculate_quality_score(result4)

        # High quality result should have a high score
        assert score1 > 0.7
        # Low quality result should have a lower score
        assert score2 < 0.6
        # Explicit quality score should be weighted heavily
        assert 0.55 < score3 < 0.65
        # Result with an error should have a low score
        assert score4 < 0.4

    def test_identify_conflicts(self, coordinator):
        """Test identifying conflicts between results."""
        # Create results with conflicts
        results = {
            "cycle1": {
                "approach": "Use a database",
                "quality_score": 0.7
            },
            "cycle2": {
                "approach": "Use a file system",
                "quality_score": 0.6
            },
            "cycle3": {
                "approach": "Use a database",  # Same as cycle1
                "quality_score": 0.5
            }
        }

        # Identify conflicts
        conflicts = coordinator._identify_conflicts(results)

        # Check that conflicts were identified
        assert "approach" in conflicts
        assert len(conflicts["approach"]) == 2  # Two different approaches

        # Check that the database approach group has two cycles
        db_group = None
        fs_group = None
        for approach_key, group in conflicts["approach"]:
            if "database" in approach_key:
                db_group = group
            elif "file system" in approach_key:
                fs_group = group

        assert db_group is not None
        assert fs_group is not None
        assert len(db_group) == 2  # cycle1 and cycle3
        assert len(fs_group) == 1  # cycle2

    def test_resolve_conflict(self, coordinator):
        """Test resolving conflicts between results."""
        # Create conflicting results
        conflict = [
            ("database", [
                ("cycle1", {
                    "approach": "Use a database",
                    "quality_score": 0.7
                }),
                ("cycle3", {
                    "approach": "Use a database",
                    "quality_score": 0.5
                })
            ]),
            ("file_system", [
                ("cycle2", {
                    "approach": "Use a file system",
                    "quality_score": 0.6
                })
            ])
        ]

        # Resolve the conflict
        resolved = coordinator._resolve_conflict(conflict)

        # Check that the conflict was resolved
        assert "primary_approach" in resolved
        assert "alternative_approaches" in resolved
        assert "resolution_method" in resolved
        assert "resolution_notes" in resolved

        # The primary approach should be the highest quality one (database with 0.7)
        assert resolved["primary_approach"]["cycle_id"] == "cycle1"
        assert resolved["primary_approach"]["quality_score"] == 0.7

        # There should be two alternative approaches
        assert len(resolved["alternative_approaches"]) == 2

        # The resolution method should be quality-based selection
        assert resolved["resolution_method"] == "quality_based_selection"


class TestRecursionMetrics:
    """Test the metrics for recursion effectiveness."""

    def test_calculate_recursion_metrics_no_children(self, coordinator):
        """Test calculating recursion metrics with no child cycles."""
        # Calculate metrics
        metrics = coordinator._calculate_recursion_metrics()

        # Check basic metrics
        assert metrics["total_cycles"] == 1
        assert metrics["max_depth"] == 0
        assert metrics["cycles_by_depth"] == {0: 1}

        # Effectiveness metrics should be default values
        assert metrics["effectiveness_score"] == 0.0
        assert metrics["improvement_rate"] == 0.0
        assert metrics["convergence_rate"] == 0.0

    def test_calculate_recursion_metrics_with_children(self, coordinator):
        """Test calculating recursion metrics with child cycles."""
        # Create child cycles
        child1 = MagicMock()
        child1.recursion_depth = 1
        child1.results = {
            "AGGREGATED": {
                "quality_score": 0.7
            }
        }

        child2 = MagicMock()
        child2.recursion_depth = 1
        child2.results = {
            "AGGREGATED": {
                "quality_score": 0.9
            }
        }

        child3 = MagicMock()
        child3.recursion_depth = 2
        child3.results = {
            "AGGREGATED": {
                "quality_score": 0.8
            }
        }

        # Add child cycles to coordinator
        coordinator.child_cycles = [child1, child2, child3]

        # Calculate metrics
        metrics = coordinator._calculate_recursion_metrics()

        # Check basic metrics
        assert metrics["total_cycles"] == 4
        assert metrics["max_depth"] == 0  # Coordinator's own depth
        assert metrics["cycles_by_depth"] == {0: 1, 1: 2, 2: 1}

        # Check effectiveness metrics
        assert metrics["improvement_rate"] == 0.8  # Average of 0.7, 0.9, 0.8
        assert 0.7 < metrics["convergence_rate"] < 0.9  # Based on standard deviation
        assert 0.5 < metrics["effectiveness_score"] < 0.9  # Weighted combination

    def test_aggregate_results_with_metrics(self, coordinator):
        """Test that aggregating results includes recursion metrics."""
        # Create child cycles
        child = MagicMock()
        child.recursion_depth = 1
        child.parent_phase = Phase.EXPAND
        child.results = {
            "EXPAND": {
                "ideas": ["Idea 1", "Idea 2"]
            }
        }

        # Add child cycle to coordinator
        coordinator.child_cycles = [child]

        # Set up phase results
        coordinator.results = {
            "EXPAND": {
                "ideas": ["Parent Idea 1", "Parent Idea 2"]
            }
        }

        # Set up performance metrics
        coordinator.performance_metrics = {
            "EXPAND": {"duration": 10},
            "DIFFERENTIATE": {"duration": 20}
        }

        # Aggregate results
        coordinator._aggregate_results()

        # Check that recursion metrics were added to performance metrics
        assert "TOTAL" in coordinator.performance_metrics
        assert "recursion_metrics" in coordinator.performance_metrics["TOTAL"]

        # Check that the metrics include the expected keys
        metrics = coordinator.performance_metrics["TOTAL"]["recursion_metrics"]
        assert "total_cycles" in metrics
        assert "max_depth" in metrics
        assert "cycles_by_depth" in metrics
        assert "effectiveness_score" in metrics
        assert "improvement_rate" in metrics
        assert "convergence_rate" in metrics
