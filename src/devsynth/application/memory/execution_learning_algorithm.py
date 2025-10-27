"""
Execution Learning Algorithm for Code Comprehension

This module implements learning algorithms that analyze execution trajectories
to build internal models of code behavior, addressing the shallow understanding
problem identified in the research literature.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .execution_trajectory_collector import ExecutionTrace, ExecutionStep
from ...domain.models.memory import MemeticUnit, MemeticMetadata, MemeticSource, CognitiveType
from ...logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


@dataclass
class ExecutionPattern:
    """Represents a learned pattern from execution trajectories."""
    pattern_id: str
    pattern_type: str  # "function_behavior", "variable_lifecycle", "error_handling", etc.
    trigger_conditions: Dict[str, Any]
    expected_outcomes: Dict[str, Any]
    confidence: float
    frequency: int
    examples: List[str] = field(default_factory=list)
    semantic_fingerprint: str = ""
    source_traces: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "trigger_conditions": self.trigger_conditions,
            "expected_outcomes": self.expected_outcomes,
            "confidence": self.confidence,
            "frequency": self.frequency,
            "examples": self.examples,
            "semantic_fingerprint": self.semantic_fingerprint,
            "source_traces": self.source_traces
        }


@dataclass
class SemanticUnderstanding:
    """Enhanced semantic understanding learned from execution patterns."""
    entity_id: str
    semantic_components: Dict[str, Any]
    behavioral_patterns: List[ExecutionPattern]
    confidence_score: float
    learning_iterations: int
    validation_results: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "entity_id": self.entity_id,
            "semantic_components": self.semantic_components,
            "behavioral_patterns": [pattern.to_dict() for pattern in self.behavioral_patterns],
            "confidence_score": self.confidence_score,
            "learning_iterations": self.learning_iterations,
            "validation_results": self.validation_results
        }


class ExecutionLearningAlgorithm:
    """Algorithm for learning from execution trajectories."""

    def __init__(self, min_pattern_frequency: int = 3, confidence_threshold: float = 0.7):
        """Initialize the learning algorithm."""
        self.min_pattern_frequency = min_pattern_frequency
        self.confidence_threshold = confidence_threshold
        self.learned_patterns: Dict[str, ExecutionPattern] = {}
        self.semantic_understandings: Dict[str, SemanticUnderstanding] = {}
        self.pattern_library = PatternLibrary()

        logger.info(f"Execution learning algorithm initialized (min_freq: {min_pattern_frequency}, threshold: {confidence_threshold})")

    def train_on_trajectories(self, trajectories: List[ExecutionTrace], learning_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Train understanding model on execution trajectories."""
        if not trajectories:
            return {"error": "No trajectories provided for training"}

        learning_config = learning_config or {}
        max_iterations = learning_config.get("max_iterations", 100)

        # Phase 1: Extract basic patterns
        patterns = self._extract_patterns_from_trajectories(trajectories)

        # Phase 2: Learn behavioral patterns
        behavioral_patterns = self._learn_behavioral_patterns(patterns)

        # Phase 3: Build semantic understanding
        semantic_understandings = self._build_semantic_understanding(trajectories, behavioral_patterns)

        # Phase 4: Validate and refine
        validation_results = self._validate_learning(trajectories, semantic_understandings)

        # Phase 5: Consolidate knowledge
        consolidated_patterns = self._consolidate_patterns(behavioral_patterns, validation_results)

        learning_results = {
            "trajectories_processed": len(trajectories),
            "patterns_extracted": len(patterns),
            "behavioral_patterns_learned": len(behavioral_patterns),
            "semantic_understandings_built": len(semantic_understandings),
            "validation_score": statistics.mean(validation_results.values()) if validation_results else 0.0,
            "learning_iterations": min(max_iterations, len(trajectories) * 10),
            "patterns": consolidated_patterns,
            "understandings": semantic_understandings
        }

        logger.info(f"Training complete: {learning_results['patterns_extracted']} patterns, {learning_results['validation_score']:.2f} validation score")
        return learning_results

    def _extract_patterns_from_trajectories(self, trajectories: List[ExecutionTrace]) -> Dict[str, Any]:
        """Extract basic patterns from execution trajectories."""
        patterns = {
            "function_calls": defaultdict(list),
            "variable_changes": defaultdict(list),
            "control_flow": defaultdict(list),
            "error_patterns": defaultdict(list),
            "performance_patterns": defaultdict(list)
        }

        for trace in trajectories:
            # Extract function call patterns
            for step in trace.execution_steps:
                for func_call in step.function_calls:
                    patterns["function_calls"][func_call].append({
                        "trace_id": str(trace.trace_id),
                        "step": step.step_number,
                        "line": step.line_number,
                        "context": step.code_line,
                        "outcome": "success" if not trace.execution_error else "error"
                    })

            # Extract variable change patterns
            for var_name, changes in trace.variable_changes.items():
                patterns["variable_changes"][var_name].extend(changes)

            # Extract control flow patterns
            for step in trace.execution_steps:
                if any(keyword in step.code_line.lower() for keyword in ["if", "for", "while", "try"]):
                    patterns["control_flow"]["control_structure"].append({
                        "trace_id": str(trace.trace_id),
                        "line": step.line_number,
                        "type": "control_flow",
                        "code": step.code_line
                    })

            # Extract error patterns
            if trace.execution_error:
                error_type = self._classify_error_pattern(trace.execution_error)
                patterns["error_patterns"][error_type].append({
                    "trace_id": str(trace.trace_id),
                    "error": trace.execution_error,
                    "code": trace.code
                })

            # Extract performance patterns
            perf_category = self._categorize_execution_performance(trace.execution_time)
            patterns["performance_patterns"][perf_category].append({
                "trace_id": str(trace.trace_id),
                "execution_time": trace.execution_time,
                "line_count": len(trace.execution_steps),
                "error": trace.execution_error is not None
            })

        return patterns

    def _learn_behavioral_patterns(self, patterns: Dict[str, Any]) -> List[ExecutionPattern]:
        """Learn behavioral patterns from extracted patterns."""
        behavioral_patterns = []

        # Learn function behavior patterns
        for func_name, calls in patterns["function_calls"].items():
            if len(calls) >= self.min_pattern_frequency:
                success_rate = sum(1 for call in calls if call["outcome"] == "success") / len(calls)

                if success_rate >= self.confidence_threshold:
                    pattern = ExecutionPattern(
                        pattern_id=f"func_behavior_{func_name}",
                        pattern_type="function_behavior",
                        trigger_conditions={"function_name": func_name},
                        expected_outcomes={"success_rate": success_rate},
                        confidence=success_rate,
                        frequency=len(calls),
                        examples=[call["context"] for call in calls[:3]],
                        source_traces=[call["trace_id"] for call in calls[:5]]
                    )
                    behavioral_patterns.append(pattern)

        # Learn variable lifecycle patterns
        for var_name, changes in patterns["variable_changes"].items():
            if len(changes) >= self.min_pattern_frequency:
                # Analyze variable change patterns
                change_types = [self._classify_variable_change(change) for change in changes]
                most_common_change = max(set(change_types), key=change_types.count) if change_types else "unknown"

                pattern = ExecutionPattern(
                    pattern_id=f"var_lifecycle_{var_name}",
                    pattern_type="variable_lifecycle",
                    trigger_conditions={"variable_name": var_name},
                    expected_outcomes={"common_change_type": most_common_change},
                    confidence=len(changes) / 10,  # Normalize by expected frequency
                    frequency=len(changes),
                    examples=changes[:3] if changes else []
                )
                behavioral_patterns.append(pattern)

        # Learn error handling patterns
        for error_type, errors in patterns["error_patterns"].items():
            if len(errors) >= self.min_pattern_frequency:
                pattern = ExecutionPattern(
                    pattern_id=f"error_pattern_{error_type}",
                    pattern_type="error_handling",
                    trigger_conditions={"error_type": error_type},
                    expected_outcomes={"occurrence_rate": len(errors) / len(patterns["function_calls"])},
                    confidence=min(1.0, len(errors) / 5),  # Normalize by frequency
                    frequency=len(errors),
                    examples=[error["code"][:100] for error in errors[:3]]
                )
                behavioral_patterns.append(pattern)

        logger.info(f"Learned {len(behavioral_patterns)} behavioral patterns")
        return behavioral_patterns

    def _build_semantic_understanding(self, trajectories: List[ExecutionTrace], patterns: List[ExecutionPattern]) -> Dict[str, SemanticUnderstanding]:
        """Build semantic understanding from trajectories and patterns."""
        understandings = {}

        # Group trajectories by code similarity
        code_groups = self._group_similar_code(trajectories)

        for group_id, group_trajectories in code_groups.items():
            # Extract semantic components from the code group
            semantic_components = self._extract_semantic_components(group_trajectories)

            # Find relevant patterns for this group
            relevant_patterns = self._find_relevant_patterns(patterns, semantic_components)

            # Build understanding
            understanding = SemanticUnderstanding(
                entity_id=group_id,
                semantic_components=semantic_components,
                behavioral_patterns=relevant_patterns,
                confidence_score=self._calculate_understanding_confidence(relevant_patterns, group_trajectories),
                learning_iterations=len(group_trajectories)
            )

            understandings[group_id] = understanding

        return understandings

    def _group_similar_code(self, trajectories: List[ExecutionTrace]) -> Dict[str, List[ExecutionTrace]]:
        """Group trajectories by code similarity."""
        groups = defaultdict(list)

        for trace in trajectories:
            # Simple grouping by code length and function count
            code_signature = self._generate_code_signature(trace.code)
            groups[code_signature].append(trace)

        return dict(groups)

    def _generate_code_signature(self, code: str) -> str:
        """Generate signature for code similarity grouping."""
        import hashlib

        # Count lines and functions as signature
        lines = code.strip().split('\n')
        line_count = len(lines)

        # Count function definitions
        function_count = code.count('def ')

        # Create signature
        signature = f"lines_{line_count}_funcs_{function_count}"
        return hashlib.md5(signature.encode()).hexdigest()[:8]

    def _extract_semantic_components(self, trajectories: List[ExecutionTrace]) -> Dict[str, Any]:
        """Extract semantic components from trajectories."""
        if not trajectories:
            return {}

        # Aggregate execution patterns
        all_steps = []
        for trace in trajectories:
            all_steps.extend(trace.execution_steps)

        # Extract function call patterns
        function_calls = {}
        for step in all_steps:
            for func_call in step.function_calls:
                function_calls[func_call] = function_calls.get(func_call, 0) + 1

        # Extract variable patterns
        variables = set()
        for trace in trajectories:
            for var_name in trace.variable_changes.keys():
                variables.add(var_name)

        # Extract error patterns
        errors = []
        for trace in trajectories:
            if trace.execution_error:
                errors.append(self._classify_error_pattern(trace.execution_error))

        return {
            "function_calls": dict(sorted(function_calls.items(), key=lambda x: x[1], reverse=True)[:10]),
            "variables": sorted(list(variables))[:10],
            "error_types": list(set(errors)),
            "avg_execution_time": statistics.mean(t.execution_time for t in trajectories),
            "success_rate": sum(1 for t in trajectories if not t.execution_error) / len(trajectories)
        }

    def _find_relevant_patterns(self, patterns: List[ExecutionPattern], components: Dict[str, Any]) -> List[ExecutionPattern]:
        """Find patterns relevant to the given semantic components."""
        relevant_patterns = []

        # Match patterns based on function calls
        if "function_calls" in components:
            for pattern in patterns:
                if pattern.pattern_type == "function_behavior":
                    for func_name in components["function_calls"]:
                        if func_name in pattern.trigger_conditions.get("function_name", ""):
                            relevant_patterns.append(pattern)
                            break

        # Match patterns based on variables
        if "variables" in components:
            for pattern in patterns:
                if pattern.pattern_type == "variable_lifecycle":
                    for var_name in components["variables"]:
                        if var_name in pattern.trigger_conditions.get("variable_name", ""):
                            relevant_patterns.append(pattern)
                            break

        return relevant_patterns

    def _calculate_understanding_confidence(self, patterns: List[ExecutionPattern], trajectories: List[ExecutionTrace]) -> float:
        """Calculate confidence in semantic understanding."""
        if not patterns or not trajectories:
            return 0.0

        # Base confidence on pattern quality
        pattern_confidences = [p.confidence for p in patterns]
        avg_pattern_confidence = statistics.mean(pattern_confidences) if pattern_confidences else 0.0

        # Boost confidence for multiple trajectories
        trajectory_diversity = min(1.0, len(trajectories) / 5)  # Normalize to 5+ trajectories

        # Boost confidence for successful executions
        success_rate = sum(1 for t in trajectories if not t.execution_error) / len(trajectories)

        return min(1.0, (avg_pattern_confidence * 0.5 + trajectory_diversity * 0.3 + success_rate * 0.2))

    def _validate_learning(self, trajectories: List[ExecutionTrace], understandings: Dict[str, SemanticUnderstanding]) -> Dict[str, float]:
        """Validate learning results against trajectories."""
        validation_scores = {}

        for group_id, understanding in understandings.items():
            # Find trajectories for this understanding
            group_trajectories = [t for t in trajectories if self._generate_code_signature(t.code) == group_id]

            if not group_trajectories:
                validation_scores[group_id] = 0.0
                continue

            # Validate pattern predictions
            prediction_accuracy = self._validate_pattern_predictions(understanding.behavioral_patterns, group_trajectories)

            # Validate semantic component extraction
            component_accuracy = self._validate_semantic_components(understanding.semantic_components, group_trajectories)

            # Combine validation scores
            overall_score = (prediction_accuracy * 0.6 + component_accuracy * 0.4)
            validation_scores[group_id] = overall_score

        return validation_scores

    def _validate_pattern_predictions(self, patterns: List[ExecutionPattern], trajectories: List[ExecutionTrace]) -> float:
        """Validate how well patterns predict trajectory outcomes."""
        if not patterns:
            return 0.0

        correct_predictions = 0
        total_predictions = 0

        for pattern in patterns:
            if pattern.pattern_type == "function_behavior":
                # Check if pattern correctly predicts function behavior
                relevant_trajectories = [
                    t for t in trajectories
                    if any(pattern.trigger_conditions.get("function_name", "") in step.code_line
                          for step in t.execution_steps)
                ]

                if relevant_trajectories:
                    # Check prediction accuracy for success rate
                    expected_success_rate = pattern.expected_outcomes.get("success_rate", 0.5)
                    actual_success_rate = sum(1 for t in relevant_trajectories if not t.execution_error) / len(relevant_trajectories)

                    # Allow some tolerance for prediction accuracy
                    if abs(expected_success_rate - actual_success_rate) < 0.2:
                        correct_predictions += 1

                    total_predictions += 1

        return correct_predictions / total_predictions if total_predictions > 0 else 0.0

    def _validate_semantic_components(self, components: Dict[str, Any], trajectories: List[ExecutionTrace]) -> float:
        """Validate semantic component extraction accuracy."""
        if not components or not trajectories:
            return 0.0

        # Check function call extraction accuracy
        extracted_functions = set(components.get("function_calls", {}).keys())
        actual_functions = set()

        for trace in trajectories:
            for step in trace.execution_steps:
                actual_functions.update(step.function_calls)

        if extracted_functions or actual_functions:
            overlap = len(extracted_functions.intersection(actual_functions))
            union = len(extracted_functions.union(actual_functions))
            return overlap / union if union > 0 else 0.0

        return 0.5  # Neutral score if no functions to compare

    def _consolidate_patterns(self, patterns: List[ExecutionPattern], validation_results: Dict[str, float]) -> Dict[str, ExecutionPattern]:
        """Consolidate patterns based on validation results."""
        consolidated = {}

        for pattern in patterns:
            # Only keep patterns that meet confidence threshold
            if pattern.confidence >= self.confidence_threshold:
                # Update confidence based on validation
                if pattern.pattern_id in validation_results:
                    pattern.confidence = min(1.0, pattern.confidence * 0.8 + validation_results[pattern.pattern_id] * 0.2)

                consolidated[pattern.pattern_id] = pattern

        # Update pattern library
        self.pattern_library.update_patterns(consolidated.values())

        return consolidated

    def predict_execution_outcome(self, code: str, learned_patterns: Dict[str, ExecutionPattern]) -> Dict[str, Any]:
        """Predict execution outcome for new code based on learned patterns."""
        # Extract semantic components from code
        code_signature = self._generate_code_signature(code)
        components = self._extract_semantic_components_from_code(code)

        # Find relevant patterns
        relevant_patterns = self._find_relevant_patterns(list(learned_patterns.values()), components)

        # Make predictions
        predictions = {
            "predicted_success_rate": 0.5,
            "predicted_execution_time": 1.0,
            "predicted_error_types": [],
            "confidence": 0.0,
            "supporting_patterns": []
        }

        if relevant_patterns:
            # Aggregate predictions from relevant patterns
            success_rates = [p.expected_outcomes.get("success_rate", 0.5) for p in relevant_patterns]
            predictions["predicted_success_rate"] = statistics.mean(success_rates)

            # Calculate overall confidence
            pattern_confidences = [p.confidence for p in relevant_patterns]
            predictions["confidence"] = statistics.mean(pattern_confidences)

            # Collect supporting patterns
            predictions["supporting_patterns"] = [
                {
                    "pattern_id": p.pattern_id,
                    "pattern_type": p.pattern_type,
                    "confidence": p.confidence,
                    "frequency": p.frequency
                }
                for p in relevant_patterns
            ]

        return predictions

    def _extract_semantic_components_from_code(self, code: str) -> Dict[str, Any]:
        """Extract semantic components from code string."""
        components = {
            "function_calls": {},
            "variables": set(),
            "control_structures": []
        }

        # Simple parsing to extract components
        lines = code.strip().split('\n')

        for line in lines:
            line = line.strip()

            # Extract function calls
            if '(' in line and ')' in line:
                # Look for function call patterns
                import re
                func_matches = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', line)
                for func in func_matches:
                    components["function_calls"][func] = components["function_calls"].get(func, 0) + 1

            # Extract variable assignments
            if '=' in line and not line.startswith('def ') and not line.startswith('class '):
                var_match = re.match(r'\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=', line)
                if var_match:
                    components["variables"].add(var_match.group(1))

            # Extract control structures
            if any(keyword in line for keyword in ['if', 'for', 'while', 'try', 'except']):
                components["control_structures"].append(line)

        components["variables"] = list(components["variables"])
        return components

    def _classify_error_pattern(self, error_message: str) -> str:
        """Classify error message into pattern categories."""
        error_lower = error_message.lower()

        if any(keyword in error_lower for keyword in ["nameerror", "undefined", "not defined"]):
            return "undefined_variable"
        elif any(keyword in error_lower for keyword in ["typeerror", "type", "cannot"]):
            return "type_mismatch"
        elif any(keyword in error_lower for keyword in ["valueerror", "invalid", "value"]):
            return "invalid_value"
        elif any(keyword in error_lower for keyword in ["indexerror", "index", "range"]):
            return "index_out_of_range"
        elif any(keyword in error_lower for keyword in ["keyerror", "key", "not found"]):
            return "missing_key"
        elif any(keyword in error_lower for keyword in ["attributeerror", "attribute"]):
            return "missing_attribute"
        elif any(keyword in error_lower for keyword in ["importerror", "import", "module"]):
            return "import_error"
        elif any(keyword in error_lower for keyword in ["syntaxerror", "syntax"]):
            return "syntax_error"
        else:
            return "unknown_error"

    def _classify_variable_change(self, change: Any) -> str:
        """Classify type of variable change."""
        if isinstance(change, (int, float)):
            return "numeric"
        elif isinstance(change, str):
            return "string"
        elif isinstance(change, (list, tuple)):
            return "sequence"
        elif isinstance(change, dict):
            return "mapping"
        elif isinstance(change, bool):
            return "boolean"
        else:
            return "object"

    def _categorize_execution_performance(self, execution_time: float) -> str:
        """Categorize execution time into performance categories."""
        if execution_time < 0.1:
            return "very_fast"
        elif execution_time < 1.0:
            return "fast"
        elif execution_time < 5.0:
            return "moderate"
        elif execution_time < 15.0:
            return "slow"
        else:
            return "very_slow"

    def create_memetic_units_from_learning(self, learning_results: Dict[str, Any]) -> List[MemeticUnit]:
        """Create Memetic Units from learning results."""
        units = []

        # Create semantic units for learned patterns
        patterns = learning_results.get("patterns", {})
        for pattern_id, pattern in patterns.items():
            semantic_unit = MemeticUnit(
                metadata=MemeticMetadata(
                    source=MemeticSource.CODE_EXECUTION,
                    cognitive_type=CognitiveType.SEMANTIC,
                    content_hash=pattern.pattern_id,
                    topic=f"execution_pattern_{pattern.pattern_type}",
                    keywords=self._extract_pattern_keywords(pattern.to_dict()),
                    confidence_score=pattern.confidence,
                    summary=f"Learned execution pattern: {pattern.pattern_type}"
                ),
                payload=pattern.to_dict()
            )
            units.append(semantic_unit)

        # Create procedural units for executable knowledge
        understandings = learning_results.get("understandings", {})
        for understanding_id, understanding in understandings.items():
            procedural_unit = MemeticUnit(
                metadata=MemeticMetadata(
                    source=MemeticSource.CODE_EXECUTION,
                    cognitive_type=CognitiveType.PROCEDURAL,
                    content_hash=understanding.entity_id,
                    topic="code_behavior_model",
                    keywords=["execution", "behavior", "pattern", "understanding"],
                    confidence_score=understanding.confidence_score,
                    summary=f"Semantic understanding of code behavior: {understanding_id}"
                ),
                payload=understanding.to_dict()
            )
            units.append(procedural_unit)

        logger.info(f"Created {len(units)} Memetic Units from learning results")
        return units

    def _extract_pattern_keywords(self, pattern_data: Dict[str, Any]) -> List[str]:
        """Extract keywords from pattern data."""
        keywords = []

        # Extract from pattern type
        keywords.append(pattern_data.get("pattern_type", ""))

        # Extract from trigger conditions
        for key, value in pattern_data.get("trigger_conditions", {}).items():
            keywords.append(str(key))
            keywords.append(str(value))

        # Extract from examples
        for example in pattern_data.get("examples", [])[:3]:
            keywords.extend(str(example).split()[:2])  # First 2 words from each example

        return keywords[:10]  # Limit to 10 keywords


class PatternLibrary:
    """Library for storing and retrieving learned execution patterns."""

    def __init__(self):
        """Initialize pattern library."""
        self.patterns: Dict[str, ExecutionPattern] = {}
        self.pattern_index: Dict[str, List[str]] = defaultdict(list)

        logger.info("Pattern library initialized")

    def update_patterns(self, new_patterns: List[ExecutionPattern]) -> None:
        """Update pattern library with new patterns."""
        for pattern in new_patterns:
            self.patterns[pattern.pattern_id] = pattern

            # Update indexes
            self.pattern_index["type"][pattern.pattern_type].append(pattern.pattern_id)
            self.pattern_index["confidence"][f"confidence_{pattern.confidence:.1f}"].append(pattern.pattern_id)

        logger.debug(f"Updated pattern library with {len(new_patterns)} new patterns")

    def find_matches(self, semantic_components: Dict[str, Any], min_confidence: float = 0.5) -> List[ExecutionPattern]:
        """Find patterns that match the given semantic components."""
        matching_patterns = []

        for pattern in self.patterns.values():
            if pattern.confidence < min_confidence:
                continue

            # Check if pattern matches components
            match_score = self._calculate_pattern_match_score(pattern, semantic_components)

            if match_score > 0.6:  # Match threshold
                pattern.match_score = match_score  # Add match score to pattern
                matching_patterns.append(pattern)

        # Sort by match score and confidence
        matching_patterns.sort(key=lambda p: (p.match_score, p.confidence), reverse=True)

        return matching_patterns

    def _calculate_pattern_match_score(self, pattern: ExecutionPattern, components: Dict[str, Any]) -> float:
        """Calculate how well a pattern matches the given components."""
        score = 0.0
        matches = 0

        # Check function call matches
        if "function_calls" in components and pattern.pattern_type == "function_behavior":
            for func_name in components["function_calls"]:
                if func_name in pattern.trigger_conditions.get("function_name", ""):
                    score += 0.5
                    matches += 1

        # Check variable matches
        if "variables" in components and pattern.pattern_type == "variable_lifecycle":
            for var_name in components["variables"]:
                if var_name in pattern.trigger_conditions.get("variable_name", ""):
                    score += 0.4
                    matches += 1

        # Normalize by number of components checked
        if matches > 0:
            score = score / matches

        return min(1.0, score)

    def get_patterns_by_type(self, pattern_type: str) -> List[ExecutionPattern]:
        """Get all patterns of a specific type."""
        pattern_ids = self.pattern_index["type"].get(pattern_type, [])
        return [self.patterns[pid] for pid in pattern_ids if pid in self.patterns]

    def get_high_confidence_patterns(self, min_confidence: float = 0.8) -> List[ExecutionPattern]:
        """Get patterns with high confidence scores."""
        return [pattern for pattern in self.patterns.values() if pattern.confidence >= min_confidence]

    def export_patterns(self) -> Dict[str, Any]:
        """Export all patterns for persistence."""
        return {
            "patterns": {pid: pattern.to_dict() for pid, pattern in self.patterns.items()},
            "index": dict(self.pattern_index),
            "total_patterns": len(self.patterns)
        }

    def import_patterns(self, pattern_data: Dict[str, Any]) -> None:
        """Import patterns from external source."""
        patterns_dict = pattern_data.get("patterns", {})

        for pattern_id, pattern_info in patterns_dict.items():
            pattern = ExecutionPattern(
                pattern_id=pattern_id,
                pattern_type=pattern_info["pattern_type"],
                trigger_conditions=pattern_info["trigger_conditions"],
                expected_outcomes=pattern_info["expected_outcomes"],
                confidence=pattern_info["confidence"],
                frequency=pattern_info["frequency"],
                examples=pattern_info.get("examples", []),
                semantic_fingerprint=pattern_info.get("semantic_fingerprint", ""),
                source_traces=pattern_info.get("source_traces", [])
            )

            self.patterns[pattern_id] = pattern

        logger.info(f"Imported {len(patterns_dict)} patterns into library")
