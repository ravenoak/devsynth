"""
Enhanced Phase Transitions for EDRR Framework.

This module provides enhanced phase transition logic, quality scoring, and metrics
collection for the EDRR (Expand, Differentiate, Refine, Reflect) framework.
"""

import re
import statistics
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from devsynth.core import CoreValues, check_report_for_value_conflicts
from devsynth.exceptions import DevSynthError
from devsynth.logging_setup import DevSynthLogger
from devsynth.methodology.base import Phase

logger = DevSynthLogger(__name__)


class PhaseTransitionError(DevSynthError):
    """Error raised when there's an issue with phase transitions."""

    pass


class QualityThreshold(Enum):
    """Quality thresholds for phase transitions."""

    LOW = 0.3
    MEDIUM = 0.5
    HIGH = 0.7
    VERY_HIGH = 0.85


class MetricType(Enum):
    """Types of metrics collected during phase transitions."""

    QUALITY = "quality"
    COMPLETENESS = "completeness"
    CONSISTENCY = "consistency"
    COVERAGE = "coverage"
    PERFORMANCE = "performance"
    CONFLICTS = "conflicts"
    DURATION = "duration"


class PhaseTransitionMetrics:
    """Collect and analyze metrics for phase transitions."""

    def __init__(self, thresholds: dict[str, dict[str, float]] | None = None):
        """Initialize the metrics collection.

        Args:
            thresholds: Optional dictionary to override default thresholds.
        """
        self.metrics = {
            Phase.EXPAND.name: {},
            Phase.DIFFERENTIATE.name: {},
            Phase.REFINE.name: {},
            Phase.RETROSPECT.name: {},
        }
        default_thresholds = {
            Phase.EXPAND.name: {
                MetricType.QUALITY.value: QualityThreshold.MEDIUM.value,
                MetricType.COMPLETENESS.value: QualityThreshold.MEDIUM.value,
                MetricType.CONSISTENCY.value: QualityThreshold.MEDIUM.value,
                MetricType.CONFLICTS.value: 3,
            },
            Phase.DIFFERENTIATE.name: {
                MetricType.QUALITY.value: QualityThreshold.MEDIUM.value,
                MetricType.COMPLETENESS.value: QualityThreshold.MEDIUM.value,
                MetricType.CONSISTENCY.value: QualityThreshold.HIGH.value,
                MetricType.CONFLICTS.value: 2,
            },
            Phase.REFINE.name: {
                MetricType.QUALITY.value: QualityThreshold.HIGH.value,
                MetricType.COMPLETENESS.value: QualityThreshold.HIGH.value,
                MetricType.CONSISTENCY.value: QualityThreshold.HIGH.value,
                MetricType.COVERAGE.value: QualityThreshold.MEDIUM.value,
                MetricType.CONFLICTS.value: 1,
            },
            Phase.RETROSPECT.name: {
                MetricType.QUALITY.value: QualityThreshold.HIGH.value,
                MetricType.COMPLETENESS.value: QualityThreshold.VERY_HIGH.value,
                MetricType.CONSISTENCY.value: QualityThreshold.VERY_HIGH.value,
                MetricType.CONFLICTS.value: 0,
            },
        }
        if thresholds:
            for phase_name, values in thresholds.items():
                phase_key = phase_name.upper()
                if phase_key in default_thresholds:
                    default_thresholds[phase_key].update(values)
        self.thresholds = default_thresholds

        self.start_times: dict[str, datetime] = {}
        self.history: list[dict[str, Any]] = []
        self.recovery_hooks: dict[str, list[Any]] = {
            phase: [] for phase in self.metrics
        }
        self.failure_hooks: dict[str, list[Any]] = {phase: [] for phase in self.metrics}

    def configure_thresholds(self, phase: Phase, thresholds: dict[str, float]) -> None:
        """Override thresholds for ``phase``."""
        self.thresholds.setdefault(phase.name, {}).update(thresholds)

    def get_thresholds(self, phase: Phase) -> dict[str, float]:
        """Return configured thresholds for ``phase``."""
        return self.thresholds.get(phase.name, {})

    def register_failure_hook(self, phase: Phase, hook: Any) -> None:
        """Register a hook executed when a phase fails to meet thresholds."""
        self.failure_hooks.setdefault(phase.name, []).append(hook)

    def start_phase(self, phase: Phase) -> None:
        """
        Record the start of a phase.

        Args:
            phase: The phase that is starting
        """
        self.start_times[phase.name] = datetime.now()
        self.history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "phase": phase.name,
                "action": "start",
                "metrics": {},
            }
        )

    def end_phase(self, phase: Phase, metrics: dict[str, Any]) -> None:
        """
        Record the end of a phase with metrics.

        Args:
            phase: The phase that is ending
            metrics: The metrics collected during the phase
        """
        end_time = datetime.now()
        start_time = self.start_times.get(phase.name)

        if start_time:
            duration = (end_time - start_time).total_seconds()
            metrics[MetricType.DURATION.value] = duration

        self.metrics[phase.name] = metrics

        self.history.append(
            {
                "timestamp": end_time.isoformat(),
                "phase": phase.name,
                "action": "end",
                "metrics": metrics,
            }
        )

    def get_phase_metrics(self, phase: Phase) -> dict[str, Any]:
        """
        Get the metrics for a specific phase.

        Args:
            phase: The phase to get metrics for

        Returns:
            The metrics for the specified phase
        """
        return self.metrics.get(phase.name, {})

    def get_all_metrics(self) -> dict[str, dict[str, Any]]:
        """
        Get all metrics for all phases.

        Returns:
            A dictionary mapping phase names to phase metrics
        """
        return self.metrics

    def get_history(self) -> list[dict[str, Any]]:
        """
        Get the history of phase transitions and metrics.

        Returns:
            A list of dictionaries containing phase transition history
        """
        return self.history

    def register_recovery_hook(self, phase: Phase, hook: Any) -> None:
        """Register a recovery hook for ``phase``.

        Hooks receive the metrics dictionary for the phase and may mutate it
        in-place.  A hook should return a dictionary. If ``{"recovered": True}``
        is returned, no further hooks will be executed.
        """

        self.recovery_hooks.setdefault(phase.name, []).append(hook)

    def _check_thresholds(
        self, metrics: dict[str, Any], thresholds: dict[str, Any]
    ) -> tuple[bool, dict[str, Any]]:
        reasons: dict[str, Any] = {}
        all_met = True
        for metric_type, threshold in thresholds.items():
            if metric_type not in metrics:
                reasons[metric_type] = "Missing metric"
                all_met = False
                continue

            metric_value = metrics[metric_type]
            if metric_type == MetricType.CONFLICTS.value:
                if metric_value > threshold:
                    reasons[metric_type] = (
                        f"Too many conflicts: {metric_value} > {threshold}"
                    )
                    all_met = False
                else:
                    reasons[metric_type] = (
                        f"Conflicts within threshold: {metric_value} <= {threshold}"
                    )
            else:
                if metric_value < threshold:
                    reasons[metric_type] = (
                        f"Below threshold: {metric_value} < {threshold}"
                    )
                    all_met = False
                else:
                    reasons[metric_type] = (
                        f"Meets threshold: {metric_value} >= {threshold}"
                    )
        return all_met, reasons

    def _execute_recovery_hooks(self, phase: Phase) -> dict[str, Any]:
        hooks = self.recovery_hooks.get(phase.name, [])
        metrics = self.metrics.get(phase.name, {})
        info: dict[str, Any] = {"recovered": False}
        for hook in hooks:
            try:
                result = hook(metrics)
                if isinstance(result, dict):
                    metrics.update(result.get("metrics", {}))
                    info.update({k: v for k, v in result.items() if k != "metrics"})
                    if result.get("recovered"):
                        info["recovered"] = True
                        break
            except Exception as e:  # pragma: no cover - defensive
                logger.debug(f"Recovery hook failed: {e}")
        return info

    def _execute_failure_hooks(self, phase: Phase) -> None:
        """Run hooks when a phase fails to meet thresholds."""
        hooks = self.failure_hooks.get(phase.name, [])
        metrics = self.metrics.get(phase.name, {})
        for hook in hooks:
            try:
                hook(metrics)
            except Exception as e:  # pragma: no cover - defensive
                logger.debug(f"Failure hook failed: {e}")

    def should_transition(self, phase: Phase) -> tuple[bool, dict[str, Any]]:
        """
        Determine if a phase should transition to the next phase based on metrics.

        Args:
            phase: The current phase

        Returns:
            A tuple containing:
                - A boolean indicating if the phase should transition
                - A dictionary containing the reasons for the decision
        """
        if phase.name not in self.metrics:
            return False, {"reason": "No metrics available for phase"}

        metrics = self.metrics[phase.name]
        thresholds = self.thresholds[phase.name]
        all_met, reasons = self._check_thresholds(metrics, thresholds)
        if all_met:
            return True, reasons

        recovery_info = self._execute_recovery_hooks(phase)
        if recovery_info.get("recovered"):
            all_met, reasons = self._check_thresholds(metrics, thresholds)
            reasons["recovery"] = "metrics recovered"
            return all_met, reasons

        self._execute_failure_hooks(phase)
        reasons["recovery"] = "recovery hooks did not recover"
        return False, reasons


def calculate_enhanced_quality_score(result: Any) -> float:
    """
    Calculate an enhanced quality score for a result.

    This function provides a more sophisticated quality scoring mechanism that
    considers various factors like completeness, consistency, and alignment with
    core values.

    Args:
        result: The result to calculate a quality score for

    Returns:
        A quality score between 0 and 1
    """
    if not isinstance(result, dict):
        return 0.5  # Default score for non-dictionary results

    try:
        # Check for explicit quality score first - if it's high, give it more weight
        explicit_score = _extract_explicit_quality_score(result)
        if explicit_score > 0.8:
            # For very high explicit scores, we want to ensure the final score is high
            # but still consider other factors
            return max(0.75, explicit_score * 0.9)

        # Start with a base score
        score = 0.5

        # 1. Completeness - more keys and deeper structure is generally better
        completeness_score = _calculate_completeness_score(result)

        # 2. Consistency - check for internal consistency
        consistency_score = _calculate_consistency_score(result)

        # 3. Core values alignment - check alignment with core values
        core_values_score = _calculate_core_values_score(result)

        # 4. Error indicators
        error_penalty = _calculate_error_penalty(result)

        # Adjust weights based on result characteristics
        # If we have a lot of content, give more weight to completeness
        content_length = len(str(result))
        if content_length > 500:
            completeness_weight = 0.35
            consistency_weight = 0.25
            core_values_weight = 0.15
            explicit_weight = 0.25
        else:
            completeness_weight = 0.25
            consistency_weight = 0.25
            core_values_weight = 0.2
            explicit_weight = 0.3

        # Combine scores with appropriate weights
        weighted_score = (
            completeness_weight * completeness_score
            + consistency_weight * consistency_score
            + core_values_weight * core_values_score
            + explicit_weight * explicit_score
        )

        # Apply error penalty
        final_score = weighted_score - error_penalty

        # Boost score for results with many positive attributes
        key_count = len(result)
        if key_count >= 5 and "error" not in result and "errors" not in result:
            final_score = min(1.0, final_score * 1.2)  # Boost by up to 20%

        # Ensure the score is between 0 and 1
        return max(0.0, min(1.0, final_score))
    except Exception:
        # If anything goes wrong, return a reasonable default
        return 0.6  # Slightly above average as a safe default


def _calculate_completeness_score(result: dict[str, Any]) -> float:
    """
    Calculate a completeness score for a result.

    Args:
        result: The result to calculate a completeness score for

    Returns:
        A completeness score between 0 and 1
    """
    # Count the number of keys
    num_keys = len(result)

    # Calculate the depth of the result
    max_depth = _calculate_max_depth(result)

    # Calculate the total content length
    content_length = len(str(result))

    # Normalize and combine these factors
    keys_score = min(1.0, num_keys / 20)  # Normalize to 0-1 range, max at 20 keys
    depth_score = min(1.0, max_depth / 5)  # Normalize to 0-1 range, max at depth 5
    length_score = min(
        1.0, content_length / 10000
    )  # Normalize to 0-1 range, max at 10000 chars

    # Combine scores with weights
    return 0.4 * keys_score + 0.3 * depth_score + 0.3 * length_score


def _calculate_max_depth(obj: Any, current_depth: int = 0) -> int:
    """
    Calculate the maximum depth of a nested structure.

    Args:
        obj: The object to calculate the depth for
        current_depth: The current depth in the recursion

    Returns:
        The maximum depth of the structure
    """
    # Handle non-iterable types and None
    if obj is None or isinstance(obj, (bool, int, float, str, bytes, type)):
        return current_depth

    if isinstance(obj, dict):
        if not obj:
            return current_depth

        # Handle each value safely
        depths = []
        for v in obj.values():
            try:
                depths.append(_calculate_max_depth(v, current_depth + 1))
            except Exception:
                # If we can't calculate depth for this value, just use current depth
                depths.append(current_depth + 1)

        return max(depths) if depths else current_depth

    elif isinstance(obj, (list, tuple, set)):
        if not obj:
            return current_depth

        # Handle each item safely
        depths = []
        for item in obj:
            try:
                depths.append(_calculate_max_depth(item, current_depth + 1))
            except Exception:
                # If we can't calculate depth for this item, just use current depth
                depths.append(current_depth + 1)

        return max(depths) if depths else current_depth

    else:
        # For any other type, just return the current depth
        return current_depth


def _calculate_consistency_score(result: dict[str, Any]) -> float:
    """
    Calculate a consistency score for a result.

    Args:
        result: The result to calculate a consistency score for

    Returns:
        A consistency score between 0 and 1
    """
    # Check for important keys that should be consistent with each other
    important_key_pairs = [
        ("approach", "implementation"),
        ("problem", "solution"),
        ("requirements", "design"),
        ("design", "implementation"),
    ]

    consistency_scores = []

    for key1, key2 in important_key_pairs:
        if key1 in result and key2 in result:
            # Calculate similarity between the two values
            similarity = _calculate_text_similarity(
                str(result[key1]), str(result[key2])
            )
            consistency_scores.append(similarity)

    # If we have no consistency scores, return a default value
    if not consistency_scores:
        return 0.5

    # Return the average consistency score
    return statistics.mean(consistency_scores)


def _calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate a simple similarity score between two texts.

    Args:
        text1: The first text
        text2: The second text

    Returns:
        A similarity score between 0 and 1
    """
    # Extract words from both texts
    words1 = set(re.findall(r"\b\w+\b", text1.lower()))
    words2 = set(re.findall(r"\b\w+\b", text2.lower()))

    # Calculate Jaccard similarity
    if not words1 and not words2:
        return 1.0  # Both empty means they're identical

    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))

    return intersection / union


def _calculate_core_values_score(result: dict[str, Any]) -> float:
    """
    Calculate a score based on alignment with core values.

    Args:
        result: The result to calculate a core values score for

    Returns:
        A core values score between 0 and 1
    """
    try:
        # Convert result to string for analysis
        result_str = str(result)

        # Check for alignment with each core value
        core_value_scores = {}

        # Safely get CoreValues - handle the case where it might not be iterable
        try:
            core_values = list(CoreValues)
        except TypeError:
            # If CoreValues is not iterable, use a default set of values
            core_values = []
            logger = DevSynthLogger(__name__)
            logger.warning("CoreValues is not iterable, using default values")

        for value in core_values:
            try:
                # Check how many times the value is mentioned
                value_name = getattr(value, "name", str(value)).lower()
                mentions = len(
                    re.findall(
                        r"\b" + re.escape(value_name) + r"\b", result_str.lower()
                    )
                )

                # Check for conflicts with this value
                try:
                    conflicts = check_report_for_value_conflicts(result_str, value)
                except Exception:
                    conflicts = []

                # Calculate a score for this value
                if conflicts:
                    core_value_scores[value_name] = max(
                        0.0, 0.5 - (0.1 * len(conflicts))
                    )
                else:
                    core_value_scores[value_name] = min(1.0, 0.5 + (0.1 * mentions))
            except Exception as e:
                # Skip this value if there's an error
                continue

        # Return the average score across all core values
        if not core_value_scores:
            return 0.5

        return statistics.mean(core_value_scores.values())
    except Exception:
        # If anything goes wrong, return a default score
        return 0.5


def _extract_explicit_quality_score(result: dict[str, Any]) -> float:
    """
    Extract an explicit quality score from a result if available.

    Args:
        result: The result to extract a quality score from

    Returns:
        A quality score between 0 and 1
    """
    # Check for explicit quality indicators
    quality_indicators = [
        "quality_score",
        "confidence",
        "accuracy",
        "reliability",
        "score",
    ]

    for indicator in quality_indicators:
        if indicator in result:
            score = result[indicator]
            if isinstance(score, (int, float)) and 0 <= score <= 1:
                return score

    # If no explicit score is found, return a default value
    return 0.5


def _calculate_error_penalty(result: dict[str, Any]) -> float:
    """
    Calculate an error penalty for a result.

    Args:
        result: The result to calculate an error penalty for

    Returns:
        An error penalty between 0 and 1
    """
    # Check for error indicators
    error_indicators = [
        "error",
        "errors",
        "failure",
        "failures",
        "exception",
        "exceptions",
    ]

    penalty = 0.0

    for indicator in error_indicators:
        if indicator in result:
            error_value = result[indicator]

            if isinstance(error_value, bool) and error_value:
                penalty += 0.2
            elif isinstance(error_value, (list, dict)) and error_value:
                penalty += min(0.5, 0.1 * len(str(error_value)))
            elif isinstance(error_value, str) and error_value:
                penalty += min(0.3, 0.05 * len(error_value))

    # Ensure the penalty is between 0 and 1
    return min(1.0, penalty)


def collect_phase_metrics(phase: Phase, results: dict[str, Any]) -> dict[str, Any]:
    """
    Collect metrics for a phase based on its results.

    Args:
        phase: The phase to collect metrics for
        results: The results of the phase

    Returns:
        A dictionary containing the collected metrics
    """
    metrics = {}

    # Calculate quality score
    quality_scores = []
    for result_id, result in results.items():
        quality_score = calculate_enhanced_quality_score(result)
        quality_scores.append(quality_score)

    if quality_scores:
        metrics[MetricType.QUALITY.value] = statistics.mean(quality_scores)
    else:
        metrics[MetricType.QUALITY.value] = 0.0

    # Calculate completeness score
    completeness_scores = []
    for result_id, result in results.items():
        if isinstance(result, dict):
            completeness_score = _calculate_completeness_score(result)
            completeness_scores.append(completeness_score)

    if completeness_scores:
        metrics[MetricType.COMPLETENESS.value] = statistics.mean(completeness_scores)
    else:
        metrics[MetricType.COMPLETENESS.value] = 0.0

    # Calculate consistency score
    consistency_scores = []
    for result_id, result in results.items():
        if isinstance(result, dict):
            consistency_score = _calculate_consistency_score(result)
            consistency_scores.append(consistency_score)

    if consistency_scores:
        metrics[MetricType.CONSISTENCY.value] = statistics.mean(consistency_scores)
    else:
        metrics[MetricType.CONSISTENCY.value] = 0.0

    # Count conflicts
    conflict_count = 0
    for result_id, result in results.items():
        if isinstance(result, dict) and "conflicts" in result:
            conflicts = result["conflicts"]
            if isinstance(conflicts, (list, dict)):
                conflict_count += len(conflicts)
            elif isinstance(conflicts, bool) and conflicts:
                conflict_count += 1

    metrics[MetricType.CONFLICTS.value] = conflict_count

    # Phase-specific metrics
    if phase == Phase.EXPAND:
        # For Expand phase, measure the diversity of ideas
        idea_diversity = _calculate_idea_diversity(results)
        metrics["idea_diversity"] = idea_diversity

    elif phase == Phase.DIFFERENTIATE:
        # For Differentiate phase, measure the categorization quality
        categorization_quality = _calculate_categorization_quality(results)
        metrics["categorization_quality"] = categorization_quality

    elif phase == Phase.REFINE:
        # For Refine phase, measure code quality if applicable
        code_quality = _calculate_code_quality(results)
        metrics["code_quality"] = code_quality

        # Measure test coverage if applicable
        test_coverage = _calculate_test_coverage(results)
        if test_coverage is not None:
            metrics[MetricType.COVERAGE.value] = test_coverage

    elif phase == Phase.RETROSPECT:
        # For Retrospect phase, measure the comprehensiveness of the retrospective
        retrospective_quality = _calculate_retrospective_quality(results)
        metrics["retrospective_quality"] = retrospective_quality

    return metrics


def _calculate_idea_diversity(results: dict[str, Any]) -> float:
    """
    Calculate the diversity of ideas in Expand phase results.

    Args:
        results: The results of the Expand phase

    Returns:
        A diversity score between 0 and 1
    """
    # Extract ideas from results
    ideas = []
    for result_id, result in results.items():
        if isinstance(result, dict):
            if "ideas" in result and isinstance(result["ideas"], list):
                ideas.extend(result["ideas"])
            elif "approaches" in result and isinstance(result["approaches"], list):
                ideas.extend(result["approaches"])
            elif "solutions" in result and isinstance(result["solutions"], list):
                ideas.extend(result["solutions"])

    if not ideas:
        return 0.5  # Default score if no ideas found

    # Calculate pairwise similarity between ideas
    similarities = []
    for i in range(len(ideas)):
        for j in range(i + 1, len(ideas)):
            similarity = _calculate_text_similarity(str(ideas[i]), str(ideas[j]))
            similarities.append(similarity)

    if not similarities:
        return 0.5  # Default score if no similarities calculated

    # Calculate diversity as 1 - average similarity
    avg_similarity = statistics.mean(similarities)
    return 1.0 - avg_similarity


def _calculate_categorization_quality(results: dict[str, Any]) -> float:
    """
    Calculate the quality of categorization in Differentiate phase results.

    Args:
        results: The results of the Differentiate phase

    Returns:
        A categorization quality score between 0 and 1
    """
    # Check for categorization in results
    categories = set()
    items_in_categories = 0

    for result_id, result in results.items():
        if isinstance(result, dict):
            # Look for category-like structures
            for key in ["categories", "groups", "classifications", "types"]:
                if key in result and isinstance(result[key], dict):
                    categories.update(result[key].keys())
                    for category, items in result[key].items():
                        if isinstance(items, list):
                            items_in_categories += len(items)

    if not categories:
        return 0.5  # Default score if no categories found

    # Calculate score based on number of categories and items
    category_count_score = min(
        1.0, len(categories) / 5
    )  # Normalize to 0-1, max at 5 categories
    items_per_category_score = min(
        1.0, items_in_categories / (len(categories) * 3)
    )  # Aim for 3 items per category

    return 0.6 * category_count_score + 0.4 * items_per_category_score


def _calculate_code_quality(results: dict[str, Any]) -> float:
    """
    Calculate the quality of code in Refine phase results.

    Args:
        results: The results of the Refine phase

    Returns:
        A code quality score between 0 and 1
    """
    # Check for code in results
    code_blocks = []

    for result_id, result in results.items():
        if isinstance(result, dict):
            # Look for code-like structures
            for key in ["code", "implementation", "solution"]:
                if key in result:
                    if isinstance(result[key], str):
                        code_blocks.append(result[key])
                    elif isinstance(result[key], dict) and "code" in result[key]:
                        code_blocks.append(result[key]["code"])

    if not code_blocks:
        return 0.5  # Default score if no code found

    # Calculate code quality based on various factors
    quality_scores = []

    for code in code_blocks:
        # Check for common code quality indicators

        # 1. Comments
        comment_lines = len(
            re.findall(
                r'^\s*#.*$|^\s*""".*?"""$|^\s*\'\'\'.*?\'\'\'$',
                code,
                re.MULTILINE | re.DOTALL,
            )
        )
        total_lines = len(code.split("\n"))
        comment_ratio = min(
            1.0, comment_lines / max(1, total_lines) * 3
        )  # Aim for 1/3 comments

        # 2. Function/method length
        function_lengths = [
            len(m.group(0).split("\n"))
            for m in re.finditer(
                r"def\s+\w+\s*\(.*?\):\s*\n(?:\s+.*?\n)+", code, re.DOTALL
            )
        ]
        if function_lengths:
            avg_function_length = statistics.mean(function_lengths)
            function_length_score = max(
                0.0, 1.0 - (avg_function_length - 15) / 50
            )  # Penalize functions longer than 15 lines
        else:
            function_length_score = 0.5

        # 3. Error handling
        error_handling_score = min(
            1.0, len(re.findall(r"try\s*:|except\s+\w+\s*:|finally\s*:", code)) / 5
        )

        # Combine scores
        code_quality_score = (
            0.3 * comment_ratio
            + 0.4 * function_length_score
            + 0.3 * error_handling_score
        )
        quality_scores.append(code_quality_score)

    return statistics.mean(quality_scores)


def _calculate_test_coverage(results: dict[str, Any]) -> float | None:
    """
    Calculate the test coverage in Refine phase results.

    Args:
        results: The results of the Refine phase

    Returns:
        A test coverage score between 0 and 1, or None if no test information is found
    """
    # Check for test coverage information in results
    for result_id, result in results.items():
        if isinstance(result, dict):
            # Look for explicit test coverage information
            if "test_coverage" in result:
                coverage = result["test_coverage"]
                if isinstance(coverage, (int, float)) and 0 <= coverage <= 100:
                    return coverage / 100

            # Look for test-related structures
            test_count = 0
            for key in ["tests", "test_cases", "unit_tests"]:
                if key in result and isinstance(result[key], list):
                    test_count += len(result[key])

            if test_count > 0:
                return min(1.0, test_count / 10)  # Normalize to 0-1, max at 10 tests

    return None  # No test information found


def _calculate_retrospective_quality(results: dict[str, Any]) -> float:
    """
    Calculate the quality of retrospective in Retrospect phase results.

    Args:
        results: The results of the Retrospect phase

    Returns:
        A retrospective quality score between 0 and 1
    """
    # Check for retrospective elements in results
    retrospective_elements = {
        "learnings": 0,
        "improvements": 0,
        "successes": 0,
        "challenges": 0,
        "next_steps": 0,
    }

    for result_id, result in results.items():
        if isinstance(result, dict):
            for element in retrospective_elements:
                if element in result:
                    if isinstance(result[element], list):
                        retrospective_elements[element] += len(result[element])
                    elif isinstance(result[element], str) and result[element]:
                        retrospective_elements[element] += 1

    # Calculate score based on presence and quantity of retrospective elements
    element_scores = []
    for element, count in retrospective_elements.items():
        element_scores.append(
            min(1.0, count / 3)
        )  # Normalize to 0-1, max at 3 items per element

    if not element_scores:
        return 0.5  # Default score if no retrospective elements found

    return statistics.mean(element_scores)
