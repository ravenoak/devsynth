"""
Execution Learning Integration with Memory System

This module integrates execution trajectory learning with the existing memory
system and enhanced knowledge graph, providing seamless enhancement of code
comprehension capabilities.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .execution_trajectory_collector import ExecutionTrajectoryCollector, ExecutionTrace
from .execution_learning_algorithm import ExecutionLearningAlgorithm, PatternLibrary
from .semantic_understanding_engine import SemanticUnderstandingEngine
from ...domain.models.memory import MemeticUnit, MemeticMetadata, MemeticSource, CognitiveType
from ...logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


class ExecutionLearningIntegration:
    """Integration between execution learning and memory systems."""

    def __init__(self, memory_manager, enhanced_graph, max_trajectories: int = 1000):
        """Initialize the execution learning integration."""
        self.memory_manager = memory_manager
        self.enhanced_graph = enhanced_graph
        self.max_trajectories = max_trajectories

        # Initialize learning components
        self.trajectory_collector = ExecutionTrajectoryCollector()
        self.learning_algorithm = ExecutionLearningAlgorithm()
        self.understanding_engine = SemanticUnderstandingEngine()
        self.pattern_library = PatternLibrary()

        # Learning state
        self.learning_history: List[Dict[str, Any]] = []
        self.understanding_cache: Dict[str, Dict[str, Any]] = {}

        logger.info(f"Execution learning integration initialized (max_trajectories: {max_trajectories})")

    def learn_from_code_execution(self, code_snippets: List[str], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Learn from code execution and enhance understanding."""
        context = context or {}

        # Phase 1: Collect execution trajectories
        trajectories = self.trajectory_collector.collect_python_trajectories(code_snippets)

        if not trajectories:
            return {"error": "No execution trajectories collected"}

        # Phase 2: Extract patterns and learn behaviors
        learning_results = self.learning_algorithm.train_on_trajectories(trajectories)

        # Phase 3: Build semantic understanding
        semantic_understandings = self.learning_algorithm._build_semantic_understanding(trajectories, learning_results["patterns"])

        # Phase 4: Create Memetic Units for storage
        episodic_units = self.trajectory_collector.create_memetic_units_from_trajectories(trajectories)
        learned_units = self.learning_algorithm.create_memetic_units_from_learning(learning_results)

        all_units = episodic_units + learned_units

        # Phase 5: Store in memory system
        self._store_learning_results(all_units, context)

        # Phase 6: Update enhanced knowledge graph
        self._enhance_knowledge_graph_with_learning(trajectories, learning_results, context)

        # Phase 7: Record learning session
        learning_session = {
            "timestamp": self._get_current_timestamp(),
            "code_snippets_count": len(code_snippets),
            "trajectories_collected": len(trajectories),
            "patterns_learned": len(learning_results["patterns"]),
            "understandings_built": len(semantic_understandings),
            "memetic_units_created": len(all_units),
            "validation_score": learning_results.get("validation_score", 0.0)
        }

        self.learning_history.append(learning_session)

        result = {
            "success": True,
            "learning_session": learning_session,
            "patterns_learned": list(learning_results["patterns"].keys()),
            "validation_score": learning_results.get("validation_score", 0.0),
            "memetic_units_stored": len(all_units)
        }

        logger.info(f"Learning complete: {result['patterns_learned']} patterns, {result['validation_score']:.2f} validation")
        return result

    def enhance_code_understanding(self, code: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Enhance understanding of code using learned patterns."""
        context = context or {}

        # Extract semantic components
        components = self.understanding_engine.extract_semantic_components(code)

        # Find relevant learned patterns
        matching_patterns = self.pattern_library.find_matches(components.to_dict())

        # Predict execution behavior
        behavior_prediction = self.understanding_engine.predict_execution_behavior(code)

        # Analyze behavioral intent
        behavioral_intent = self.understanding_engine.analyze_behavioral_intent(code)

        # Create enhanced understanding
        enhanced_understanding = {
            "code_hash": self.understanding_engine._compute_code_hash(code),
            "semantic_components": components.to_dict(),
            "behavioral_intent": behavioral_intent.to_dict(),
            "execution_prediction": behavior_prediction,
            "matching_patterns": [
                {
                    "pattern_id": p.pattern_id,
                    "pattern_type": p.pattern_type,
                    "confidence": p.confidence,
                    "frequency": p.frequency
                }
                for p in matching_patterns[:5]  # Top 5 patterns
            ],
            "understanding_confidence": self._calculate_overall_understanding_confidence(
                matching_patterns, behavior_prediction, behavioral_intent
            )
        }

        # Cache the understanding
        self.understanding_cache[code] = enhanced_understanding

        return enhanced_understanding

    def test_semantic_robustness(self, original_code: str, mutated_code: str) -> Dict[str, Any]:
        """Test semantic robustness using execution learning."""
        # Analyze both versions
        original_understanding = self.enhance_code_understanding(original_code)
        mutated_understanding = self.enhance_code_understanding(mutated_code)

        # Compare understandings
        semantic_preserved = self._compare_semantic_understanding(
            original_understanding, mutated_understanding
        )

        # Calculate understanding preservation
        understanding_preserved = semantic_preserved > 0.8  # 80% threshold

        return {
            "original_understanding": original_understanding,
            "mutated_understanding": mutated_understanding,
            "semantic_similarity": semantic_preserved,
            "understanding_preserved": understanding_preserved,
            "performance_drop": self._calculate_performance_drop(original_understanding, mutated_understanding),
            "validation_method": "semantic_preservation_test"
        }

    def _store_learning_results(self, units: List[MemeticUnit], context: Dict[str, Any]) -> None:
        """Store learning results in memory system."""
        # Store in appropriate memory layers
        for unit in units:
            # Route to appropriate layer based on cognitive type
            layer_name = self._route_to_memory_layer(unit.metadata.cognitive_type)

            try:
                # Store in memory manager
                self.memory_manager.store(
                    key=str(unit.metadata.unit_id),
                    content=unit.payload,
                    metadata={
                        "memetic_metadata": unit.to_dict(),
                        "learning_context": context,
                        "cognitive_type": unit.metadata.cognitive_type.value,
                        "source": unit.metadata.source.value
                    }
                )

                logger.debug(f"Stored Memetic Unit {unit.metadata.unit_id} in {layer_name}")

            except Exception as e:
                logger.error(f"Failed to store Memetic Unit {unit.metadata.unit_id}: {e}")

    def _enhance_knowledge_graph_with_learning(self, trajectories: List[ExecutionTrace], learning_results: Dict[str, Any], context: Dict[str, Any]) -> None:
        """Enhance knowledge graph with execution learning insights."""
        from .enhanced_knowledge_graph import Entity, IntentLink

        # Create entities for learned patterns
        for pattern_id, pattern in learning_results["patterns"].items():
            # Create semantic entity for the pattern
            pattern_entity = Entity(
                id=f"pattern_{pattern_id}",
                type="ExecutionPattern",
                properties={
                    "pattern_id": pattern_id,
                    "pattern_type": pattern.pattern_type,
                    "confidence": pattern.confidence,
                    "frequency": pattern.frequency,
                    "expected_outcomes": pattern.expected_outcomes
                },
                business_context={
                    "learning_method": "execution_trajectory_analysis",
                    "validation_score": learning_results.get("validation_score", 0.0)
                }
            )

            self.enhanced_graph.add_entity(pattern_entity)

        # Create relationships between patterns and code
        understandings = learning_results.get("understandings", {})
        for understanding_id, understanding in understandings.items():
            # Link understanding to code entities
            code_entity_id = f"code_{understanding_id}"
            understanding_entity = Entity(
                id=code_entity_id,
                type="CodeUnderstanding",
                properties={
                    "understanding_id": understanding_id,
                    "confidence_score": understanding.confidence_score,
                    "semantic_components": understanding.semantic_components
                }
            )

            self.enhanced_graph.add_entity(understanding_entity)

            # Link to relevant patterns
            for pattern in understanding.behavioral_patterns:
                self.enhanced_graph.add_relationship({
                    "source_id": code_entity_id,
                    "target_id": f"pattern_{pattern.pattern_id}",
                    "type": "IMPLEMENTED_BY",
                    "strength": pattern.confidence
                })

    def _route_to_memory_layer(self, cognitive_type: CognitiveType) -> str:
        """Route Memetic Unit to appropriate memory layer."""
        layer_mapping = {
            CognitiveType.WORKING: "working_memory",
            CognitiveType.EPISODIC: "episodic_buffer",
            CognitiveType.SEMANTIC: "semantic_store",
            CognitiveType.PROCEDURAL: "procedural_archive"
        }

        return layer_mapping.get(cognitive_type, "working_memory")

    def _calculate_overall_understanding_confidence(self, patterns: List[Any], prediction: Dict[str, Any], intent: Any) -> float:
        """Calculate overall confidence in code understanding."""
        confidences = []

        # Pattern matching confidence
        if patterns:
            pattern_confidences = [p.confidence for p in patterns]
            confidences.append(sum(pattern_confidences) / len(pattern_confidences))

        # Prediction confidence
        if prediction and "confidence" in prediction:
            confidences.append(prediction["confidence"])

        # Intent analysis confidence
        if intent and hasattr(intent, 'intent_confidence'):
            confidences.append(intent.intent_confidence)

        return sum(confidences) / len(confidences) if confidences else 0.0

    def _compare_semantic_understanding(self, understanding1: Dict[str, Any], understanding2: Dict[str, Any]) -> float:
        """Compare semantic understanding between two code versions."""
        # Compare behavioral intent
        intent1 = understanding1.get("behavioral_intent", {})
        intent2 = understanding2.get("behavioral_intent", {})

        purpose1 = intent1.get("primary_purpose", "")
        purpose2 = intent2.get("primary_purpose", "")

        purpose_similarity = 1.0 if purpose1 == purpose2 else 0.5

        # Compare semantic fingerprints
        fingerprint1 = understanding1.get("semantic_components", {}).get("semantic_fingerprint", "")
        fingerprint2 = understanding2.get("semantic_components", {}).get("semantic_fingerprint", "")

        fingerprint_similarity = 1.0 if fingerprint1 == fingerprint2 else 0.0

        # Compare pattern matching
        patterns1 = understanding1.get("matching_patterns", [])
        patterns2 = understanding2.get("matching_patterns", [])

        if patterns1 and patterns2:
            pattern_types1 = {p["pattern_type"] for p in patterns1}
            pattern_types2 = {p["pattern_type"] for p in patterns2}
            pattern_overlap = len(pattern_types1.intersection(pattern_types2))
            pattern_union = len(pattern_types1.union(pattern_types2))
            pattern_similarity = pattern_overlap / pattern_union if pattern_union > 0 else 0.0
        else:
            pattern_similarity = 0.5

        # Weighted combination
        return (purpose_similarity * 0.4 + fingerprint_similarity * 0.3 + pattern_similarity * 0.3)

    def _calculate_performance_drop(self, understanding1: Dict[str, Any], understanding2: Dict[str, Any]) -> float:
        """Calculate performance drop between understanding versions."""
        confidence1 = understanding1.get("understanding_confidence", 0.0)
        confidence2 = understanding2.get("understanding_confidence", 0.0)

        return max(0.0, confidence1 - confidence2)

    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get statistics about the learning system."""
        if not self.learning_history:
            return {"error": "No learning sessions completed"}

        # Calculate aggregate statistics
        total_sessions = len(self.learning_history)
        total_patterns = sum(session["patterns_learned"] for session in self.learning_history)
        total_understandings = sum(session["understandings_built"] for session in self.learning_history)
        avg_validation_score = sum(session["validation_score"] for session in self.learning_history) / total_sessions

        # Pattern library statistics
        pattern_stats = self.pattern_library.export_patterns()

        return {
            "learning_sessions": total_sessions,
            "total_patterns_learned": total_patterns,
            "total_understandings": total_understandings,
            "average_validation_score": avg_validation_score,
            "pattern_library_size": pattern_stats["total_patterns"],
            "cached_understandings": len(self.understanding_cache),
            "recent_session": self.learning_history[-1] if self.learning_history else None
        }

    def _get_current_timestamp(self):
        """Get current timestamp (can be overridden for testing)."""
        from datetime import datetime
        return datetime.now()

    def validate_against_research_benchmarks(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate learning results against research benchmarks."""
        benchmarks = {
            "semantic_understanding": 0.8,  # 80% semantic understanding target
            "mutation_resistance": 0.9,     # 90% resistance to semantic mutations
            "pattern_accuracy": 0.85,       # 85% pattern prediction accuracy
            "execution_prediction": 0.8     # 80% execution outcome prediction
        }

        validation_report = {
            "benchmark_comparison": {},
            "research_alignment": True,
            "improvement_areas": [],
            "validation_method": "research_benchmark_comparison"
        }

        # Compare against benchmarks
        for metric, benchmark_value in benchmarks.items():
            if metric in test_results:
                achieved_value = test_results[metric]
                meets_benchmark = achieved_value >= benchmark_value

                validation_report["benchmark_comparison"][metric] = {
                    "achieved": achieved_value,
                    "benchmark": benchmark_value,
                    "meets_benchmark": meets_benchmark,
                    "improvement_needed": max(0.0, benchmark_value - achieved_value)
                }

                if not meets_benchmark:
                    validation_report["research_alignment"] = False
                    validation_report["improvement_areas"].append(
                        f"{metric}: needs {validation_report['benchmark_comparison'][metric]['improvement_needed']:.2f} improvement"
                    )

        # Overall assessment
        benchmark_meet_count = sum(1 for b in validation_report["benchmark_comparison"].values() if b["meets_benchmark"])
        validation_report["benchmark_compliance_rate"] = benchmark_meet_count / len(benchmarks)

        return validation_report

    def export_learning_state(self) -> Dict[str, Any]:
        """Export current learning state for persistence."""
        return {
            "learning_history": self.learning_history,
            "pattern_library": self.pattern_library.export_patterns(),
            "understanding_cache": self.understanding_cache,
            "statistics": self.get_learning_statistics(),
            "export_timestamp": self._get_current_timestamp().isoformat()
        }

    def import_learning_state(self, state_data: Dict[str, Any]) -> None:
        """Import learning state from external source."""
        # Restore learning history
        self.learning_history = state_data.get("learning_history", [])

        # Restore pattern library
        pattern_data = state_data.get("pattern_library", {})
        self.pattern_library.import_patterns(pattern_data)

        # Restore understanding cache
        self.understanding_cache = state_data.get("understanding_cache", {})

        logger.info(f"Imported learning state: {len(self.learning_history)} sessions, {len(self.pattern_library.patterns)} patterns")
