"""
Cognitive Type Classifier for Memetic Units

This module provides intelligent classification of Memetic Units into appropriate
cognitive types based on content analysis, source, and context.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ...domain.models.memory import CognitiveType, MemeticSource, MemeticUnit
from ...logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


class CognitiveTypeClassifier:
    """Intelligent classifier for Memetic Unit cognitive types."""

    def __init__(self, confidence_threshold: float = 0.8):
        """Initialize the classifier with configuration."""
        self.confidence_threshold = confidence_threshold
        self.classification_history = []

        # Classification rules and patterns
        self._setup_classification_rules()

        logger.info(f"Cognitive type classifier initialized with threshold {confidence_threshold}")

    def _setup_classification_rules(self) -> None:
        """Setup classification rules and patterns."""
        # Source-based classification (highest priority)
        self.source_mapping = {
            MemeticSource.USER_INPUT: CognitiveType.WORKING,
            MemeticSource.AGENT_SELF: CognitiveType.WORKING,
            MemeticSource.LLM_RESPONSE: CognitiveType.WORKING,
            MemeticSource.CODE_EXECUTION: CognitiveType.EPISODIC,
            MemeticSource.TEST_RESULT: CognitiveType.EPISODIC,
            MemeticSource.ERROR_LOG: CognitiveType.EPISODIC,
            MemeticSource.FILE_INGESTION: CognitiveType.SEMANTIC,
            MemeticSource.DOCUMENTATION: CognitiveType.SEMANTIC,
            MemeticSource.API_RESPONSE: CognitiveType.PROCEDURAL,
            MemeticSource.METRIC_DATA: CognitiveType.EPISODIC,
            MemeticSource.CONFIGURATION: CognitiveType.SEMANTIC
        }

        # Content-based classification patterns
        self.content_patterns = {
            CognitiveType.WORKING: [
                "task", "current", "active", "immediate", "working",
                "prompt", "response", "conversation", "chat"
            ],
            CognitiveType.EPISODIC: [
                "execution", "result", "output", "error", "trace",
                "log", "event", "timestamp", "history", "experience"
            ],
            CognitiveType.SEMANTIC: [
                "knowledge", "concept", "pattern", "documentation",
                "reference", "guide", "tutorial", "example", "definition"
            ],
            CognitiveType.PROCEDURAL: [
                "procedure", "process", "workflow", "step", "instruction",
                "api", "function", "method", "algorithm", "skill"
            ]
        }

        # Context-based classification hints
        self.context_hints = {
            "agent_context": CognitiveType.WORKING,
            "edrr_context": CognitiveType.WORKING,
            "learning_context": CognitiveType.SEMANTIC,
            "debugging_context": CognitiveType.EPISODIC,
            "documentation_context": CognitiveType.SEMANTIC,
            "testing_context": CognitiveType.EPISODIC
        }

    def classify(self, unit: MemeticUnit, context: Dict[str, Any] = None) -> CognitiveType:
        """Classify a Memetic Unit into appropriate cognitive type."""
        if context is None:
            context = {}

        # Method 1: Source-based classification (highest priority)
        source_type = self.source_mapping.get(unit.metadata.source)
        if source_type:
            source_confidence = 0.9  # High confidence for source-based classification

            # Override if context strongly suggests different type
            context_override = self._check_context_override(context)
            if context_override and source_confidence >= self.confidence_threshold:
                unit.metadata.cognitive_type = source_type
                self._record_classification(unit, source_type, "source", source_confidence)
                return source_type

        # Method 2: Content-based classification
        content_type, content_confidence = self._classify_by_content(unit.payload)
        if content_confidence >= self.confidence_threshold:
            unit.metadata.cognitive_type = content_type
            self._record_classification(unit, content_type, "content", content_confidence)
            return content_type

        # Method 3: Context-based classification
        context_type, context_confidence = self._classify_by_context(context)
        if context_confidence >= self.confidence_threshold:
            unit.metadata.cognitive_type = context_type
            self._record_classification(unit, context_type, "context", context_confidence)
            return context_type

        # Method 4: Hybrid scoring (combine multiple signals)
        hybrid_type, hybrid_confidence = self._classify_by_hybrid_scoring(unit, context)
        if hybrid_confidence >= self.confidence_threshold:
            unit.metadata.cognitive_type = hybrid_type
            self._record_classification(unit, hybrid_type, "hybrid", hybrid_confidence)
            return hybrid_type

        # Method 5: Fallback to most common type (WORKING)
        fallback_type = CognitiveType.WORKING
        unit.metadata.cognitive_type = fallback_type
        self._record_classification(unit, fallback_type, "fallback", 0.5)
        return fallback_type

    def _check_context_override(self, context: Dict[str, Any]) -> bool:
        """Check if context provides strong override signal."""
        # Check for explicit context hints
        for context_key, suggested_type in self.context_hints.items():
            if context_key in context:
                return True
        return False

    def _classify_by_content(self, payload: Any) -> tuple[CognitiveType, float]:
        """Classify based on content analysis."""
        text_content = str(payload).lower()

        # Calculate scores for each cognitive type
        type_scores = {}

        for cog_type, patterns in self.content_patterns.items():
            score = 0.0
            matches = 0

            for pattern in patterns:
                if pattern in text_content:
                    score += 1.0
                    matches += 1

            # Normalize score by number of patterns
            if patterns:
                score = score / len(patterns)

            # Bonus for multiple matches
            if matches > 1:
                score *= 1.2

            # Penalty for very short content
            if len(text_content.split()) < 5:
                score *= 0.7

            type_scores[cog_type] = score

        # Find best match
        best_type = max(type_scores.items(), key=lambda x: x[1])
        best_confidence = best_type[1]

        # Require minimum confidence
        if best_confidence < 0.3:
            return CognitiveType.WORKING, 0.0

        return best_type[0], min(1.0, best_confidence)

    def _classify_by_context(self, context: Dict[str, Any]) -> tuple[CognitiveType, float]:
        """Classify based on context information."""
        if not context:
            return CognitiveType.WORKING, 0.0

        # Check context hints
        for context_key, suggested_type in self.context_hints.items():
            if context_key in context:
                # Higher confidence if context explicitly indicates type
                confidence = 0.8 if context.get(context_key) is True else 0.6
                return suggested_type, confidence

        # Check context content for type indicators
        context_text = " ".join(str(v) for v in context.values()).lower()

        # Simple keyword matching in context
        if any(word in context_text for word in ["learn", "knowledge", "pattern"]):
            return CognitiveType.SEMANTIC, 0.6
        elif any(word in context_text for word in ["debug", "error", "log"]):
            return CognitiveType.EPISODIC, 0.6
        elif any(word in context_text for word in ["procedure", "workflow", "step"]):
            return CognitiveType.PROCEDURAL, 0.6

        return CognitiveType.WORKING, 0.4

    def _classify_by_hybrid_scoring(
        self,
        unit: MemeticUnit,
        context: Dict[str, Any]
    ) -> tuple[CognitiveType, float]:
        """Classify using hybrid scoring of multiple signals."""
        # Weight different classification methods
        source_weight = 0.4
        content_weight = 0.4
        context_weight = 0.2

        # Get scores from each method
        source_type = self.source_mapping.get(unit.metadata.source, CognitiveType.WORKING)
        source_score = 0.9 if unit.metadata.source in self.source_mapping else 0.0

        content_type, content_score = self._classify_by_content(unit.payload)
        context_type, context_score = self._classify_by_context(context)

        # Calculate weighted scores for each cognitive type
        type_scores = {}
        for cog_type in CognitiveType:
            score = 0.0

            # Source contribution
            if source_type == cog_type:
                score += source_score * source_weight

            # Content contribution
            if content_type == cog_type:
                score += content_score * content_weight

            # Context contribution
            if context_type == cog_type:
                score += context_score * context_weight

            type_scores[cog_type] = score

        # Find best match
        best_type = max(type_scores.items(), key=lambda x: x[1])
        best_confidence = best_type[1]

        # Apply minimum confidence threshold
        if best_confidence < 0.3:
            return CognitiveType.WORKING, 0.0

        return best_type[0], min(1.0, best_confidence)

    def _record_classification(
        self,
        unit: MemeticUnit,
        cog_type: CognitiveType,
        method: str,
        confidence: float
    ) -> None:
        """Record classification decision for analysis and improvement."""
        classification_record = {
            "unit_id": str(unit.metadata.unit_id),
            "source": unit.metadata.source.value,
            "cognitive_type": cog_type.value,
            "method": method,
            "confidence": confidence,
            "content_length": len(str(unit.payload)),
            "keywords": unit.metadata.keywords[:5]  # First 5 keywords
        }

        self.classification_history.append(classification_record)

        # Keep history manageable
        if len(self.classification_history) > 1000:
            self.classification_history = self.classification_history[-500:]

        logger.debug(f"Classified unit {unit.metadata.unit_id} as {cog_type.value} via {method} (confidence: {confidence:.2f})")

    def get_classification_accuracy(self) -> Dict[str, float]:
        """Get classification accuracy statistics."""
        if not self.classification_history:
            return {"total_classifications": 0}

        # Calculate method accuracy (simplified - would need ground truth for full accuracy)
        method_counts = {}
        for record in self.classification_history:
            method = record["method"]
            method_counts[method] = method_counts.get(method, 0) + 1

        # Calculate average confidence by method
        method_confidence = {}
        for record in self.classification_history:
            method = record["method"]
            confidence = record["confidence"]
            if method not in method_confidence:
                method_confidence[method] = []
            method_confidence[method].append(confidence)

        method_avg_confidence = {
            method: sum(confidences) / len(confidences)
            for method, confidences in method_confidence.items()
        }

        return {
            "total_classifications": len(self.classification_history),
            "method_distribution": method_counts,
            "average_confidence_by_method": method_avg_confidence,
            "high_confidence_classifications": sum(1 for r in self.classification_history if r["confidence"] >= self.confidence_threshold)
        }

    def suggest_improvements(self) -> List[str]:
        """Suggest improvements based on classification history."""
        suggestions = []

        stats = self.get_classification_accuracy()

        if stats["total_classifications"] < 100:
            suggestions.append("Collect more classification examples for better accuracy")
            return suggestions

        # Analyze method performance
        method_confidence = stats["average_confidence_by_method"]

        # Find lowest performing method
        if method_confidence:
            worst_method = min(method_confidence.items(), key=lambda x: x[1])
            if worst_method[1] < 0.6:
                suggestions.append(f"Improve {worst_method[0]} classification method (low confidence: {worst_method[1]:.2f})")

        # Check for classification bias
        method_distribution = stats["method_distribution"]
        if method_distribution:
            most_common_method = max(method_distribution.items(), key=lambda x: x[1])
            if most_common_method[1] > len(self.classification_history) * 0.8:
                suggestions.append(f"Reduce reliance on {most_common_method[0]} method (used {most_common_method[1]}/{len(self.classification_history)} times)")

        return suggestions

    def batch_classify(self, units: List[MemeticUnit], context: Dict[str, Any] = None) -> List[CognitiveType]:
        """Classify multiple units in batch."""
        classifications = []

        for unit in units:
            try:
                cog_type = self.classify(unit, context)
                classifications.append(cog_type)
            except Exception as e:
                logger.error(f"Failed to classify unit {unit.metadata.unit_id}: {e}")
                # Fallback to working memory
                unit.metadata.cognitive_type = CognitiveType.WORKING
                classifications.append(CognitiveType.WORKING)

        logger.info(f"Batch classified {len(units)} units")
        return classifications

    def reclassify_with_feedback(self, unit: MemeticUnit, correct_type: CognitiveType, context: Dict[str, Any] = None) -> None:
        """Reclassify unit with feedback for learning."""
        # Update unit classification
        old_type = unit.metadata.cognitive_type
        unit.metadata.cognitive_type = correct_type

        # Record feedback for improvement
        feedback_record = {
            "unit_id": str(unit.metadata.unit_id),
            "old_type": old_type.value,
            "correct_type": correct_type.value,
            "source": unit.metadata.source.value,
            "content_length": len(str(unit.payload)),
            "context": context or {}
        }

        # Store feedback for analysis (could be used for model improvement)
        logger.info(f"Reclassified unit {unit.metadata.unit_id} from {old_type.value} to {correct_type.value} based on feedback")

        # Update confidence based on feedback
        unit.metadata.confidence_score = min(1.0, unit.metadata.confidence_score + 0.1)
