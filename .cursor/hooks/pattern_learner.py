#!/usr/bin/env python3
"""
Pattern Learning and Improvement Detection System

Analyzes development patterns over time to identify improvement opportunities
and automatically suggest rule enhancements based on observed behavior.
"""

import json
import logging
import os
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import re


@dataclass
class DevelopmentPattern:
    """Represents a detected development pattern."""
    pattern_id: str
    pattern_type: str
    description: str
    frequency: int
    trend: str  # "increasing", "decreasing", "stable"
    confidence: float
    examples: List[str]
    affected_files: List[str]
    improvement_potential: float
    suggested_action: str
    first_seen: datetime
    last_seen: datetime


@dataclass
class LearningInsight:
    """Represents a learning insight from pattern analysis."""
    insight_id: str
    insight_type: str
    title: str
    description: str
    confidence: float
    impact: str  # "high", "medium", "low"
    affected_areas: List[str]
    recommended_actions: List[str]
    examples: List[str]
    created_at: datetime
    patterns: List[str]


class SessionAnalyzer:
    """Analyzes development sessions to identify patterns."""

    def __init__(self, learning_dir: Path):
        self.learning_dir = learning_dir
        self.learning_dir.mkdir(parents=True, exist_ok=True)
        self.session_data: List[Dict[str, Any]] = []
        self.patterns: Dict[str, DevelopmentPattern] = {}

        self._load_session_history()

    def _load_session_history(self):
        """Load historical session data."""
        history_file = self.learning_dir / "session_history.json"
        if history_file.exists():
            with open(history_file) as f:
                self.session_data = json.load(f).get("sessions", [])

    def _save_session_history(self):
        """Save session data to persistent storage."""
        history_file = self.learning_dir / "session_history.json"
        data = {
            "sessions": self.session_data,
            "last_updated": datetime.now().isoformat()
        }
        with open(history_file, 'w') as f:
            json.dump(data, f, indent=2)

    def record_session_event(self, event_type: str, context: Dict[str, Any]):
        """Record a session event for pattern analysis."""
        session_event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "context": context
        }
        self.session_data.append(session_event)
        self._save_session_history()

        # Analyze patterns if we have enough data
        if len(self.session_data) % 10 == 0:  # Analyze every 10 events
            self._analyze_session_patterns()

    def _analyze_session_patterns(self):
        """Analyze session data for patterns."""
        if len(self.session_data) < 10:
            return

        # Group events by type and time windows
        events_by_type = defaultdict(list)
        for event in self.session_data:
            events_by_type[event["event_type"]].append(event)

        # Analyze error patterns
        error_events = events_by_type.get("error", [])
        if error_events:
            self._analyze_error_patterns(error_events)

        # Analyze command usage patterns
        command_events = events_by_type.get("command", [])
        if command_events:
            self._analyze_command_patterns(command_events)

        # Analyze file modification patterns
        file_events = events_by_type.get("file_modified", [])
        if file_events:
            self._analyze_file_patterns(file_events)

    def _analyze_error_patterns(self, error_events: List[Dict[str, Any]]):
        """Analyze error patterns to identify improvement opportunities."""
        error_types = Counter()

        for event in error_events:
            error_msg = event.get("context", {}).get("error_message", "")
            error_type = self._categorize_error(error_msg)
            error_types[error_type] += 1

        # Look for frequent error types
        for error_type, count in error_types.items():
            if count >= 3:  # 3 or more occurrences
                pattern = DevelopmentPattern(
                    pattern_id=f"error_{error_type}",
                    pattern_type="recurring_error",
                    description=f"Frequent {error_type} errors occurring",
                    frequency=count,
                    trend="stable",
                    confidence=0.8,
                    examples=[event.get("context", {}).get("error_message", "") for event in error_events if self._categorize_error(event.get("context", {}).get("error_message", "")) == error_type][:3],
                    affected_files=[],  # Would need to extract from context
                    improvement_potential=0.9,
                    suggested_action=f"Create rule to prevent {error_type} errors",
                    first_seen=datetime.now() - timedelta(days=1),
                    last_seen=datetime.now()
                )

                self.patterns[pattern.pattern_id] = pattern

    def _analyze_command_patterns(self, command_events: List[Dict[str, Any]]):
        """Analyze command usage patterns."""
        command_usage = Counter()

        for event in command_events:
            command = event.get("context", {}).get("command_name", "")
            command_usage[command] += 1

        # Look for frequently used commands that might benefit from rules
        for command, count in command_usage.items():
            if count >= 5 and not self._is_standard_command(command):
                pattern = DevelopmentPattern(
                    pattern_id=f"command_{command}",
                    pattern_type="frequent_command",
                    description=f"Command '{command}' used frequently, may benefit from automation",
                    frequency=count,
                    trend="stable",
                    confidence=0.7,
                    examples=[command],
                    affected_files=[],
                    improvement_potential=0.6,
                    suggested_action=f"Create rule to automate {command} workflow",
                    first_seen=datetime.now() - timedelta(days=1),
                    last_seen=datetime.now()
                )

                self.patterns[pattern.pattern_id] = pattern

    def _analyze_file_patterns(self, file_events: List[Dict[str, Any]]):
        """Analyze file modification patterns."""
        file_modifications = defaultdict(list)

        for event in file_events:
            file_path = event.get("context", {}).get("file_path", "")
            if file_path:
                file_modifications[file_path].append(event)

        # Look for files that are frequently modified
        for file_path, events in file_modifications.items():
            if len(events) >= 5:
                pattern = DevelopmentPattern(
                    pattern_id=f"file_{Path(file_path).stem}",
                    pattern_type="frequently_modified",
                    description=f"File {file_path} modified frequently, may need refactoring",
                    frequency=len(events),
                    trend="stable",
                    confidence=0.6,
                    examples=[file_path],
                    affected_files=[file_path],
                    improvement_potential=0.7,
                    suggested_action=f"Consider refactoring {file_path} or creating abstraction",
                    first_seen=datetime.now() - timedelta(days=1),
                    last_seen=datetime.now()
                )

                self.patterns[pattern.pattern_id] = pattern

    def _categorize_error(self, error_message: str) -> str:
        """Categorize error messages into types."""
        error_lower = error_message.lower()

        if "import" in error_lower and ("not found" in error_lower or "module" in error_lower):
            return "import_error"
        elif "type" in error_lower and "annotation" in error_lower:
            return "type_error"
        elif "attribute" in error_lower:
            return "attribute_error"
        elif "syntax" in error_lower:
            return "syntax_error"
        elif "indentation" in error_lower:
            return "indentation_error"
        else:
            return "other_error"

    def _is_standard_command(self, command: str) -> bool:
        """Check if command is a standard system command."""
        standard_commands = {
            "expand-phase", "differentiate-phase", "refine-phase", "retrospect-phase",
            "generate-specification", "validate-bdd-scenarios", "generate-test-suite",
            "code-review", "help", "status", "config"
        }
        return command in standard_commands


class RuleImprovementDetector:
    """Detects opportunities for improving existing rules."""

    def __init__(self, rules_dir: Path, analytics_dir: Path):
        self.rules_dir = rules_dir
        self.analytics_dir = analytics_dir
        self.analytics_dir.mkdir(parents=True, exist_ok=True)

    def analyze_rule_effectiveness(self, rule_name: str) -> Dict[str, Any]:
        """Analyze how effective a rule is."""
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

        # Calculate trend
        recent_usage = data.get("recent_usage", [])
        trend = self._calculate_trend(recent_usage)

        return {
            "effectiveness": effectiveness,
            "usage_count": usage_count,
            "error_rate": error_rate,
            "trend": trend,
            "improvement_suggestions": self._generate_improvement_suggestions(rule_name, data)
        }

    def _calculate_trend(self, usage_history: List[int]) -> str:
        """Calculate usage trend."""
        if len(usage_history) < 7:
            return "insufficient_data"

        recent_avg = sum(usage_history[-7:]) / 7
        older_avg = sum(usage_history[:-7]) / max(len(usage_history) - 7, 1)

        if recent_avg > older_avg * 1.2:
            return "increasing"
        elif recent_avg < older_avg * 0.8:
            return "decreasing"
        else:
            return "stable"

    def _generate_improvement_suggestions(self, rule_name: str, data: Dict[str, Any]) -> List[str]:
        """Generate specific improvement suggestions for a rule."""
        suggestions = []

        effectiveness = data.get("effectiveness", 0.5)
        error_rate = data.get("error_rate", 0.0)
        usage_count = data.get("usage_count", 0)

        if effectiveness < 0.7:
            suggestions.append(f"Improve clarity and specificity in {rule_name}")

        if error_rate > 0.1:
            suggestions.append(f"Fix ambiguous language in {rule_name} that's causing errors")

        if usage_count == 0:
            suggestions.append(f"Rule {rule_name} is not being applied - check glob patterns")

        # Check rule content for improvement opportunities
        rule_file = self.rules_dir / f"{rule_name}.mdc"
        if rule_file.exists():
            content = rule_file.read_text()
            suggestions.extend(self._analyze_rule_content(rule_name, content))

        return suggestions

    def _analyze_rule_content(self, rule_name: str, content: str) -> List[str]:
        """Analyze rule content for improvement opportunities."""
        suggestions = []

        # Check for common issues
        if len(content) > 2000:
            suggestions.append(f"Rule {rule_name} is too long - consider breaking into smaller rules")

        if "TODO" in content or "FIXME" in content:
            suggestions.append(f"Remove placeholder comments from {rule_name}")

        if not re.search(r'## Examples?', content):
            suggestions.append(f"Add practical examples to {rule_name}")

        # Check YAML frontmatter
        if not content.startswith('---'):
            suggestions.append(f"Add proper YAML frontmatter to {rule_name}")

        return suggestions

    def identify_deprecated_rules(self) -> List[str]:
        """Identify rules that might be deprecated or need updates."""
        deprecated = []

        for rule_file in self.rules_dir.glob("*.mdc"):
            rule_name = rule_file.stem
            analysis = self.analyze_rule_effectiveness(rule_name)

            # Rule is potentially deprecated if:
            # 1. Very low usage and decreasing trend
            # 2. High error rate
            # 3. Very low effectiveness
            if (analysis["usage_count"] < 5 and analysis["trend"] == "decreasing" or
                analysis["error_rate"] > 0.3 or
                analysis["effectiveness"] < 0.3):
                deprecated.append(rule_name)

        return deprecated


class ContextAwarenessEngine:
    """Manages contextual awareness for rule application."""

    def __init__(self, learning_dir: Path):
        self.learning_dir = learning_dir
        self.context_patterns: Dict[str, Any] = {}
        self.load_context_patterns()

    def load_context_patterns(self):
        """Load learned context patterns."""
        patterns_file = self.learning_dir / "context_patterns.json"
        if patterns_file.exists():
            with open(patterns_file) as f:
                self.context_patterns = json.load(f)

    def save_context_patterns(self):
        """Save learned context patterns."""
        patterns_file = self.learning_dir / "context_patterns.json"
        with open(patterns_file, 'w') as f:
            json.dump(self.context_patterns, f, indent=2)

    def analyze_context_effectiveness(self, context: Dict[str, Any], outcome: str) -> Dict[str, Any]:
        """Analyze how well context helped achieve the desired outcome."""
        context_key = self._generate_context_key(context)

        if context_key not in self.context_patterns:
            self.context_patterns[context_key] = {
                "count": 0,
                "successful_outcomes": 0,
                "average_confidence": 0.0,
                "improvement_suggestions": []
            }

        pattern = self.context_patterns[context_key]
        pattern["count"] += 1

        if outcome == "success":
            pattern["successful_outcomes"] += 1

        # Calculate success rate
        success_rate = pattern["successful_outcomes"] / pattern["count"]

        # Generate improvement suggestions based on success rate
        if success_rate < 0.7:
            pattern["improvement_suggestions"] = self._generate_context_improvements(context, success_rate)

        self.save_context_patterns()

        return {
            "context_key": context_key,
            "success_rate": success_rate,
            "improvements": pattern["improvement_suggestions"]
        }

    def _generate_context_key(self, context: Dict[str, Any]) -> str:
        """Generate a key for context pattern."""
        # Create a normalized key from context
        key_parts = []

        for k, v in sorted(context.items()):
            if isinstance(v, list):
                key_parts.append(f"{k}:{','.join(sorted(v))}")
            else:
                key_parts.append(f"{k}:{v}")

        return "|".join(key_parts)

    def _generate_context_improvements(self, context: Dict[str, Any], success_rate: float) -> List[str]:
        """Generate suggestions for improving context effectiveness."""
        suggestions = []

        if success_rate < 0.5:
            suggestions.append("Consider adding more specific context about project requirements")
            suggestions.append("Include examples of desired behavior in context")

        if context.get("file_type") == "python" and success_rate < 0.6:
            suggestions.append("Add architectural context when working with Python files")

        if context.get("task_type") == "implementation" and success_rate < 0.6:
            suggestions.append("Include specification references for implementation tasks")

        return suggestions


class LearningEngine:
    """Main learning engine that coordinates all learning activities."""

    def __init__(self, cursor_dir: Path):
        self.cursor_dir = cursor_dir
        self.learning_dir = cursor_dir / "learning"
        self.analytics_dir = cursor_dir / "analytics"

        # Initialize components
        self.session_analyzer = SessionAnalyzer(self.learning_dir)
        self.rule_improver = RuleImprovementDetector(self.cursor_dir / "rules", self.analytics_dir)
        self.context_engine = ContextAwarenessEngine(self.learning_dir)

        # Learning state
        self.insights: List[LearningInsight] = []
        self.load_insights()

    def load_insights(self):
        """Load previous insights."""
        insights_file = self.learning_dir / "insights.json"
        if insights_file.exists():
            with open(insights_file) as f:
                data = json.load(f)
                self.insights = [LearningInsight(**insight) for insight in data.get("insights", [])]

    def save_insights(self):
        """Save insights to persistent storage."""
        insights_file = self.learning_dir / "insights.json"
        data = {
            "insights": [asdict(insight) for insight in self.insights],
            "last_updated": datetime.now().isoformat()
        }
        with open(insights_file, 'w') as f:
            json.dump(data, f, indent=2)

    def record_learning_event(self, event_type: str, context: Dict[str, Any], outcome: str = "unknown"):
        """Record a learning event."""
        self.session_analyzer.record_session_event(event_type, context)

        # Analyze context effectiveness
        context_analysis = self.context_engine.analyze_context_effectiveness(context, outcome)

        # Generate insights if significant patterns are detected
        if context_analysis["success_rate"] < 0.7 or len(self.session_analyzer.patterns) > 0:
            self._generate_insights()

    def _generate_insights(self):
        """Generate learning insights from current data."""
        new_insights = []

        # Generate insights from patterns
        for pattern in self.session_analyzer.patterns.values():
            if pattern.improvement_potential > 0.7:
                insight = LearningInsight(
                    insight_id=f"pattern_{pattern.pattern_id}",
                    insight_type="pattern_improvement",
                    title=f"Improvement Opportunity: {pattern.pattern_type}",
                    description=pattern.description,
                    confidence=pattern.confidence,
                    impact="high" if pattern.improvement_potential > 0.8 else "medium",
                    affected_areas=["development_workflow", "code_quality"],
                    recommended_actions=[pattern.suggested_action],
                    examples=pattern.examples,
                    created_at=datetime.now(),
                    patterns=[pattern.pattern_id]
                )
                new_insights.append(insight)

        # Generate insights from rule analysis
        deprecated_rules = self.rule_improver.identify_deprecated_rules()
        if deprecated_rules:
            insight = LearningInsight(
                insight_id="deprecated_rules",
                insight_type="rule_maintenance",
                title="Rule Maintenance Required",
                description=f"Found {len(deprecated_rules)} rules that may need updates or deprecation",
                confidence=0.9,
                impact="medium",
                affected_areas=["rule_management", "system_efficiency"],
                recommended_actions=[f"Review rule: {rule}" for rule in deprecated_rules],
                examples=deprecated_rules,
                created_at=datetime.now(),
                patterns=[]
            )
            new_insights.append(insight)

        # Add new insights
        self.insights.extend(new_insights)
        self.save_insights()

    def get_actionable_insights(self) -> List[LearningInsight]:
        """Get insights that require immediate action."""
        return [insight for insight in self.insights
                if insight.impact in ["high", "medium"] and insight.confidence > 0.7]

    def get_rule_improvement_suggestions(self) -> Dict[str, List[str]]:
        """Get improvement suggestions for all rules."""
        suggestions = {}

        for rule_file in (self.cursor_dir / "rules").glob("*.mdc"):
            rule_name = rule_file.stem
            analysis = self.rule_improver.analyze_rule_effectiveness(rule_name)

            if analysis["improvement_suggestions"]:
                suggestions[rule_name] = analysis["improvement_suggestions"]

        return suggestions


def trigger_learning_event(event_type: str, context: Dict[str, Any], outcome: str = "unknown"):
    """Trigger a learning event for pattern analysis."""
    cursor_dir = Path('.cursor')
    engine = LearningEngine(cursor_dir)
    engine.record_learning_event(event_type, context, outcome)


def analyze_rule_effectiveness(rule_name: str) -> Dict[str, Any]:
    """Analyze the effectiveness of a specific rule."""
    cursor_dir = Path('.cursor')
    improver = RuleImprovementDetector(cursor_dir / "rules", cursor_dir / "analytics")
    return improver.analyze_rule_effectiveness(rule_name)


def get_learning_insights() -> List[LearningInsight]:
    """Get current learning insights."""
    cursor_dir = Path('.cursor')
    engine = LearningEngine(cursor_dir)
    return engine.get_actionable_insights()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Pattern learning and improvement detection")
    parser.add_argument("--analyze-rules", action="store_true",
                       help="Analyze rule effectiveness")
    parser.add_argument("--get-insights", action="store_true",
                       help="Get actionable learning insights")
    parser.add_argument("--record-event", nargs=3, metavar=("EVENT_TYPE", "CONTEXT_KEY", "CONTEXT_VALUE"),
                       help="Record a learning event")

    args = parser.parse_args()

    if args.analyze_rules:
        cursor_dir = Path('.cursor')
        improver = RuleImprovementDetector(cursor_dir / "rules", cursor_dir / "analytics")

        print("🔍 Analyzing rule effectiveness...")
        for rule_file in (cursor_dir / "rules").glob("*.mdc"):
            rule_name = rule_file.stem
            analysis = improver.analyze_rule_effectiveness(rule_name)

            if analysis["usage_count"] > 0:
                print(f"📊 {rule_name}:")
                print(f"   Effectiveness: {analysis['effectiveness']:.2f}")
                print(f"   Usage Count: {analysis['usage_count']}")
                print(f"   Error Rate: {analysis['error_rate']:.2f}")
                print(f"   Trend: {analysis['trend']}")
                if analysis["improvement_suggestions"]:
                    print(f"   Suggestions: {analysis['improvement_suggestions']}")
                print()

    elif args.get_insights:
        insights = get_learning_insights()
        print(f"💡 Found {len(insights)} actionable insights:")

        for insight in insights:
            print(f"\n🔍 {insight.title}")
            print(f"   Type: {insight.insight_type}")
            print(f"   Impact: {insight.impact}")
            print(f"   Confidence: {insight.confidence:.2f}")
            print(f"   Description: {insight.description}")
            print(f"   Actions: {insight.recommended_actions}")

    elif args.record_event:
        event_type, context_key, context_value = args.record_event
        context = {context_key: context_value}
        trigger_learning_event(event_type, context)
        print(f"📝 Recorded learning event: {event_type} with context {context}")

    else:
        print("Pattern Learning System")
        print("Use --analyze-rules to analyze rule effectiveness")
        print("Use --get-insights to get learning insights")
        print("Use --record-event to record a learning event")
