#!/usr/bin/env python3
"""
Cursor Hooks Manager for Self-Improvement System

This module implements Cursor's Hooks system (v1.7+) to provide dynamic rule management,
automated improvement detection, and self-evolving rule capabilities.

Hooks are triggered at specific lifecycle events and can modify agent behavior,
suggest rule improvements, and maintain rule quality over time.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum


class HookEvent(Enum):
    """Cursor lifecycle events that can trigger hooks."""
    RULE_LOADED = "rule_loaded"
    RULE_APPLIED = "rule_applied"
    COMMAND_EXECUTED = "command_executed"
    CODE_GENERATED = "code_generated"
    CODE_REVIEWED = "code_reviewed"
    ERROR_OCCURRED = "error_occurred"
    PATTERN_DETECTED = "pattern_detected"
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"


class ImprovementType(Enum):
    """Types of improvements that can be suggested."""
    RULE_ENHANCEMENT = "rule_enhancement"
    NEW_RULE = "new_rule"
    RULE_DEPRECATION = "rule_deprecation"
    PATTERN_RECOGNITION = "pattern_recognition"
    CONTEXT_IMPROVEMENT = "context_improvement"
    QUALITY_GATE = "quality_gate"


@dataclass
class HookContext:
    """Context information passed to hooks."""
    event: HookEvent
    timestamp: datetime
    session_id: str
    user_id: str
    project_path: str
    rule_name: Optional[str] = None
    command_name: Optional[str] = None
    file_path: Optional[str] = None
    code_snippet: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['event'] = self.event.value
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class ImprovementSuggestion:
    """Represents a suggested improvement to the rule system."""
    improvement_type: ImprovementType
    title: str
    description: str
    confidence: float  # 0.0 to 1.0
    priority: int  # 1 (low) to 5 (critical)
    affected_rules: List[str]
    suggested_changes: Dict[str, Any]
    rationale: str
    examples: List[str]
    created_at: datetime
    context: HookContext

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['improvement_type'] = self.improvement_type.value
        data['created_at'] = self.created_at.isoformat()
        data['context'] = self.context.to_dict()
        return data


class RuleQualityAnalyzer:
    """Analyzes rule effectiveness and suggests improvements."""

    def __init__(self, rules_dir: Path, analytics_dir: Path):
        self.rules_dir = rules_dir
        self.analytics_dir = analytics_dir
        self.analytics_dir.mkdir(parents=True, exist_ok=True)

    def analyze_rule_effectiveness(self, rule_name: str) -> Dict[str, Any]:
        """Analyze how effective a rule is based on usage patterns."""
        analytics_file = self.analytics_dir / f"{rule_name}_analytics.json"

        if not analytics_file.exists():
            return {"effectiveness": 0.5, "usage_count": 0, "error_rate": 0.0}

        with open(analytics_file) as f:
            data = json.load(f)

        usage_count = data.get("usage_count", 0)
        successful_applications = data.get("successful_applications", 0)
        errors = data.get("errors", 0)

        if usage_count == 0:
            return {"effectiveness": 0.5, "usage_count": 0, "error_rate": 0.0}

        effectiveness = successful_applications / usage_count
        error_rate = errors / usage_count

        return {
            "effectiveness": effectiveness,
            "usage_count": usage_count,
            "error_rate": error_rate,
            "trend": self._calculate_trend(data)
        }

    def _calculate_trend(self, data: Dict) -> str:
        """Calculate usage trend over time."""
        recent_usage = data.get("recent_usage", [])
        if len(recent_usage) < 2:
            return "stable"

        recent_avg = sum(recent_usage[-7:]) / min(len(recent_usage), 7)
        older_avg = sum(recent_usage[:-7]) / max(len(recent_usage) - 7, 1)

        if recent_avg > older_avg * 1.2:
            return "increasing"
        elif recent_avg < older_avg * 0.8:
            return "decreasing"
        else:
            return "stable"


class PatternDetector:
    """Detects patterns in code and behavior that could benefit from new rules."""

    def __init__(self, patterns_dir: Path):
        self.patterns_dir = patterns_dir
        self.patterns_dir.mkdir(parents=True, exist_ok=True)

    def detect_repetitive_patterns(self, code_snippet: str) -> List[Dict[str, Any]]:
        """Detect patterns that could be automated with rules."""
        patterns = []

        # Detect common patterns
        if "TODO" in code_snippet or "FIXME" in code_snippet:
            patterns.append({
                "type": "todo_comments",
                "description": "TODO/FIXME comments suggest missing documentation",
                "confidence": 0.8,
                "suggested_rule": "todo_comment_validation"
            })

        if "print(" in code_snippet and "debug" in code_snippet.lower():
            patterns.append({
                "type": "debug_code",
                "description": "Debug print statements left in production code",
                "confidence": 0.9,
                "suggested_rule": "debug_code_removal"
            })

        return patterns

    def detect_error_patterns(self, error_message: str, context: HookContext) -> List[Dict[str, Any]]:
        """Detect error patterns that could be prevented with better rules."""
        patterns = []

        if "import" in error_message.lower() and "not found" in error_message.lower():
            patterns.append({
                "type": "import_error",
                "description": "Import errors suggest missing import rules",
                "confidence": 0.7,
                "suggested_rule": "import_organization"
            })

        if "type" in error_message.lower() and "annotation" in error_message.lower():
            patterns.append({
                "type": "type_annotation",
                "description": "Type annotation issues suggest type checking rules",
                "confidence": 0.8,
                "suggested_rule": "type_annotation_enforcement"
            })

        return patterns


class RuleEvolutionManager:
    """Manages the evolution and improvement of rules over time."""

    def __init__(self, rules_dir: Path, learning_dir: Path):
        self.rules_dir = rules_dir
        self.learning_dir = learning_dir
        self.learning_dir.mkdir(parents=True, exist_ok=True)

    def suggest_rule_improvements(self, rule_name: str, feedback: Dict[str, Any]) -> List[str]:
        """Suggest specific improvements to a rule based on feedback."""
        improvements = []

        # Analyze rule content and usage
        rule_file = self.rules_dir / f"{rule_name}.mdc"
        if not rule_file.exists():
            return improvements

        content = rule_file.read_text()

        # Check for common improvement opportunities
        if "TODO" in content or "FIXME" in content:
            improvements.append(f"Remove placeholder comments from {rule_name}")

        if len(content) > 2000:
            improvements.append(f"Consider breaking down large rule {rule_name} into smaller, focused rules")

        if feedback.get("error_rate", 0) > 0.1:
            improvements.append(f"Improve clarity in {rule_name} to reduce errors")

        return improvements

    def create_improved_rule(self, base_rule: str, improvements: List[str]) -> str:
        """Create an improved version of a rule."""
        # This would implement rule improvement logic
        # For now, return a placeholder
        return f"# Improved version of {base_rule}\n# Improvements: {', '.join(improvements)}"


class HookManager:
    """Main hook manager that coordinates all hook activities."""

    def __init__(self, cursor_dir: Path):
        self.cursor_dir = cursor_dir
        self.hooks_dir = cursor_dir / "hooks"
        self.analytics_dir = cursor_dir / "analytics"
        self.patterns_dir = cursor_dir / "patterns"
        self.learning_dir = cursor_dir / "learning"

        # Initialize components
        self.quality_analyzer = RuleQualityAnalyzer(self.cursor_dir / "rules", self.analytics_dir)
        self.pattern_detector = PatternDetector(self.patterns_dir)
        self.evolution_manager = RuleEvolutionManager(self.cursor_dir / "rules", self.learning_dir)

        # Hook registry
        self.hooks: Dict[HookEvent, List[Callable]] = {event: [] for event in HookEvent}
        self.improvements_history: List[ImprovementSuggestion] = []

        # Load existing improvements
        self._load_improvements_history()

        # Register default hooks
        self._register_default_hooks()

    def _load_improvements_history(self):
        """Load previous improvement suggestions."""
        history_file = self.learning_dir / "improvements_history.json"
        if history_file.exists():
            with open(history_file) as f:
                data = json.load(f)
                self.improvements_history = [
                    ImprovementSuggestion(**item) for item in data.get("improvements", [])
                ]

    def _save_improvements_history(self):
        """Save improvement suggestions to persistent storage."""
        history_file = self.learning_dir / "improvements_history.json"
        data = {
            "improvements": [improvement.to_dict() for improvement in self.improvements_history],
            "last_updated": datetime.now().isoformat()
        }
        with open(history_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _register_default_hooks(self):
        """Register the default set of hooks."""
        self.register_hook(HookEvent.CODE_GENERATED, self._code_generation_hook)
        self.register_hook(HookEvent.ERROR_OCCURRED, self._error_occurrence_hook)
        self.register_hook(HookEvent.SESSION_ENDED, self._session_end_hook)
        self.register_hook(HookEvent.PATTERN_DETECTED, self._pattern_detection_hook)

    def register_hook(self, event: HookEvent, hook_func: Callable):
        """Register a hook function for a specific event."""
        if event not in self.hooks:
            self.hooks[event] = []
        self.hooks[event].append(hook_func)

    def trigger_hook(self, event: HookEvent, context: HookContext) -> List[ImprovementSuggestion]:
        """Trigger all hooks for a specific event."""
        suggestions = []

        if event in self.hooks:
            for hook_func in self.hooks[event]:
                try:
                    result = hook_func(context)
                    if result:
                        if isinstance(result, list):
                            suggestions.extend(result)
                        else:
                            suggestions.append(result)
                except Exception as e:
                    logging.error(f"Hook {hook_func.__name__} failed: {e}")

        # Filter and prioritize suggestions
        suggestions = self._filter_and_prioritize_suggestions(suggestions)

        # Add to history
        self.improvements_history.extend(suggestions)
        self._save_improvements_history()

        return suggestions

    def _filter_and_prioritize_suggestions(self, suggestions: List[ImprovementSuggestion]) -> List[ImprovementSuggestion]:
        """Filter and prioritize improvement suggestions."""
        # Remove duplicates and low-confidence suggestions
        filtered = []
        seen_titles = set()

        for suggestion in suggestions:
            if suggestion.confidence < 0.6:
                continue

            if suggestion.title in seen_titles:
                # Keep the one with higher confidence
                existing = next(s for s in filtered if s.title == suggestion.title)
                if suggestion.confidence > existing.confidence:
                    filtered.remove(existing)
                    filtered.append(suggestion)
            else:
                filtered.append(suggestion)
                seen_titles.add(suggestion.title)

        # Sort by priority and confidence
        filtered.sort(key=lambda x: (x.priority, x.confidence), reverse=True)

        return filtered[:10]  # Keep top 10 suggestions

    def _code_generation_hook(self, context: HookContext) -> Optional[ImprovementSuggestion]:
        """Hook triggered when code is generated."""
        if not context.code_snippet:
            return None

        patterns = self.pattern_detector.detect_repetitive_patterns(context.code_snippet)

        if patterns:
            return ImprovementSuggestion(
                improvement_type=ImprovementType.PATTERN_RECOGNITION,
                title="Pattern Detected in Generated Code",
                description=f"Detected patterns that could benefit from new rules: {patterns}",
                confidence=0.8,
                priority=3,
                affected_rules=["code_generation"],
                suggested_changes={"new_rules": patterns},
                rationale="Automated pattern detection for rule improvement",
                examples=[context.code_snippet[:200] + "..."],
                created_at=datetime.now(),
                context=context
            )

        return None

    def _error_occurrence_hook(self, context: HookContext) -> Optional[ImprovementSuggestion]:
        """Hook triggered when an error occurs."""
        if not context.error_message:
            return None

        patterns = self.pattern_detector.detect_error_patterns(context.error_message, context)

        if patterns:
            return ImprovementSuggestion(
                improvement_type=ImprovementType.RULE_ENHANCEMENT,
                title="Error Pattern Detected",
                description=f"Error pattern suggests rule improvement: {context.error_message}",
                confidence=0.9,
                priority=4,
                affected_rules=["error_handling", "validation"],
                suggested_changes={"error_prevention": patterns},
                rationale="Error analysis for proactive rule improvement",
                examples=[context.error_message],
                created_at=datetime.now(),
                context=context
            )

        return None

    def _session_end_hook(self, context: HookContext) -> List[ImprovementSuggestion]:
        """Hook triggered when a session ends - comprehensive analysis."""
        suggestions = []

        # Analyze rule effectiveness
        for rule_file in (self.cursor_dir / "rules").glob("*.mdc"):
            rule_name = rule_file.stem
            analysis = self.quality_analyzer.analyze_rule_effectiveness(rule_name)

            if analysis["effectiveness"] < 0.7:
                suggestions.append(ImprovementSuggestion(
                    improvement_type=ImprovementType.RULE_ENHANCEMENT,
                    title=f"Improve Rule Effectiveness: {rule_name}",
                    description=f"Rule {rule_name} has low effectiveness ({analysis['effectiveness']:.2f})",
                    confidence=0.8,
                    priority=2,
                    affected_rules=[rule_name],
                    suggested_changes={"effectiveness_improvement": analysis},
                    rationale="Rule effectiveness analysis",
                    examples=[],
                    created_at=datetime.now(),
                    context=context
                ))

        return suggestions

    def _pattern_detection_hook(self, context: HookContext) -> Optional[ImprovementSuggestion]:
        """Hook for general pattern detection."""
        # This could be extended for more sophisticated pattern detection
        return None

    def get_pending_improvements(self) -> List[ImprovementSuggestion]:
        """Get all pending improvement suggestions."""
        return [s for s in self.improvements_history if s.priority >= 3]

    def get_rule_analytics(self, rule_name: str) -> Dict[str, Any]:
        """Get analytics for a specific rule."""
        return self.quality_analyzer.analyze_rule_effectiveness(rule_name)

    def apply_improvement(self, suggestion: ImprovementSuggestion) -> bool:
        """Apply an approved improvement suggestion."""
        try:
            # Implementation would depend on the specific improvement type
            # For now, log the improvement
            improvement_log = self.learning_dir / "applied_improvements.json"

            applied_improvements = []
            if improvement_log.exists():
                with open(improvement_log) as f:
                    applied_improvements = json.load(f)

            applied_improvements.append({
                **suggestion.to_dict(),
                "applied_at": datetime.now().isoformat(),
                "status": "applied"
            })

            with open(improvement_log, 'w') as f:
                json.dump(applied_improvements, f, indent=2)

            return True
        except Exception as e:
            logging.error(f"Failed to apply improvement: {e}")
            return False


def create_hook_context(
    event: HookEvent,
    session_id: str = "default",
    user_id: str = "current_user",
    **kwargs
) -> HookContext:
    """Create a hook context with the given parameters."""
    return HookContext(
        event=event,
        timestamp=datetime.now(),
        session_id=session_id,
        user_id=user_id,
        project_path=str(Path.cwd()),
        **kwargs
    )


# Global hook manager instance
_hook_manager: Optional[HookManager] = None


def get_hook_manager() -> HookManager:
    """Get the global hook manager instance."""
    global _hook_manager
    if _hook_manager is None:
        cursor_dir = Path('.cursor')
        _hook_manager = HookManager(cursor_dir)
    return _hook_manager


def trigger_hook(event: HookEvent, **context_kwargs) -> List[ImprovementSuggestion]:
    """Trigger a hook with the given event and context."""
    manager = get_hook_manager()
    context = create_hook_context(event, **context_kwargs)
    return manager.trigger_hook(event, context)


# Convenience functions for common hook triggers
def on_code_generated(code_snippet: str, file_path: str = None) -> List[ImprovementSuggestion]:
    """Trigger hook when code is generated."""
    return trigger_hook(
        HookEvent.CODE_GENERATED,
        code_snippet=code_snippet,
        file_path=file_path
    )


def on_error_occurred(error_message: str, context: str = None) -> List[ImprovementSuggestion]:
    """Trigger hook when an error occurs."""
    return trigger_hook(
        HookEvent.ERROR_OCCURRED,
        error_message=error_message,
        metadata={"context": context}
    )


def on_session_end(session_data: Dict[str, Any]) -> List[ImprovementSuggestion]:
    """Trigger hook when session ends."""
    return trigger_hook(
        HookEvent.SESSION_ENDED,
        metadata={"session_data": session_data}
    )
