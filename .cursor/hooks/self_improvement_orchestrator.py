#!/usr/bin/env python3
"""
Self-Improvement Orchestrator for Cursor Rules

Coordinates all self-improvement systems including hooks, pattern detection,
rule validation, analytics, and learning to create a comprehensive
self-evolving rule system.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from analytics_monitor import generate_rule_analytics, get_system_analytics
from auto_rule_generator import RuleSuggestion, analyze_and_suggest_rules
from hook_manager import HookContext, HookEvent, HookManager, ImprovementSuggestion
from pattern_learner import LearningEngine, get_learning_insights
from rule_validator import RuleImprovement, generate_health_report


class SelfImprovementOrchestrator:
    """Main orchestrator for the self-improvement system."""

    def __init__(self, cursor_dir: Path):
        self.cursor_dir = cursor_dir
        self.hooks_dir = cursor_dir / "hooks"
        self.analytics_dir = cursor_dir / "analytics"
        self.learning_dir = cursor_dir / "learning"

        # Initialize components
        self.hook_manager = HookManager(cursor_dir)
        self.learning_engine = LearningEngine(cursor_dir)

        # State management
        self.last_analysis = datetime.now()
        self.analysis_frequency = timedelta(hours=1)  # Analyze every hour
        self.improvements_applied = 0
        self.rules_generated = 0

        # Load state
        self._load_state()

    def _load_state(self):
        """Load orchestrator state."""
        state_file = self.learning_dir / "orchestrator_state.json"
        if state_file.exists():
            with open(state_file) as f:
                state = json.load(f)
                self.last_analysis = datetime.fromisoformat(state["last_analysis"])
                self.improvements_applied = state["improvements_applied"]
                self.rules_generated = state["rules_generated"]

    def _save_state(self):
        """Save orchestrator state."""
        state_file = self.learning_dir / "orchestrator_state.json"
        state = {
            "last_analysis": self.last_analysis.isoformat(),
            "improvements_applied": self.improvements_applied,
            "rules_generated": self.rules_generated,
            "last_updated": datetime.now().isoformat(),
        }
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)

    def run_full_analysis(self) -> dict[str, Any]:
        """Run comprehensive analysis of the rule system."""
        print("🔄 Running comprehensive self-improvement analysis...")

        analysis_results = {
            "timestamp": datetime.now().isoformat(),
            "system_health": {},
            "rule_improvements": [],
            "new_rule_suggestions": [],
            "learning_insights": [],
            "analytics_summary": {},
            "actions_taken": [],
            "recommendations": [],
        }

        # 1. System health analysis
        print("📊 Analyzing system health...")
        health_report = generate_health_report(
            str(self.cursor_dir / "rules"), str(self.analytics_dir)
        )
        analysis_results["system_health"] = health_report

        # 2. Rule improvements
        print("🔧 Analyzing rule improvements...")
        improvements = self._analyze_rule_improvements()
        analysis_results["rule_improvements"] = improvements

        # 3. New rule suggestions
        print("💡 Generating new rule suggestions...")
        new_rules = self._generate_new_rules()
        analysis_results["new_rule_suggestions"] = new_rules

        # 4. Learning insights
        print("🧠 Collecting learning insights...")
        insights = get_learning_insights()
        analysis_results["learning_insights"] = [
            insight.__dict__ for insight in insights
        ]

        # 5. Analytics summary
        print("📈 Collecting analytics...")
        analytics = get_system_analytics(24)  # Last 24 hours
        analysis_results["analytics_summary"] = analytics

        # 6. Apply automatic improvements
        print("🚀 Applying automatic improvements...")
        actions = self._apply_automatic_improvements(improvements, new_rules)
        analysis_results["actions_taken"] = actions

        # 7. Generate recommendations
        print("💡 Generating recommendations...")
        recommendations = self._generate_recommendations(analysis_results)
        analysis_results["recommendations"] = recommendations

        # Update state
        self.last_analysis = datetime.now()
        self._save_state()

        print(f"✅ Analysis complete! Found {len(recommendations)} recommendations.")
        return analysis_results

    def _analyze_rule_improvements(self) -> list[dict[str, Any]]:
        """Analyze existing rules for improvement opportunities."""
        from rule_validator import generate_rule_improvements

        improvements = generate_rule_improvements(
            str(self.cursor_dir / "rules"), min_score=0.8
        )

        return [
            {
                "rule_name": imp.rule_name,
                "improvement_type": imp.improvement_type,
                "impact_score": imp.impact_score,
                "confidence": imp.confidence,
                "description": imp.description,
                "improved_content_preview": imp.improved_content[:200] + "...",
            }
            for imp in improvements
        ]

    def _generate_new_rules(self) -> list[dict[str, Any]]:
        """Generate suggestions for new rules based on codebase analysis."""
        source_dirs = ["src", "tests", "docs"]
        suggestions = analyze_and_suggest_rules(
            source_dirs, str(self.cursor_dir / "rules")
        )

        return [
            {
                "rule_name": s.rule_name,
                "description": s.description,
                "confidence": s.confidence,
                "priority": s.priority,
                "pattern_type": s.patterns[0].pattern_type if s.patterns else "unknown",
                "affected_files": (
                    len(s.patterns[0].affected_files) if s.patterns else 0
                ),
            }
            for s in suggestions
            if s.confidence > 0.7
        ]

    def _apply_automatic_improvements(
        self, rule_improvements: list[dict], new_rules: list[dict]
    ) -> list[str]:
        """Apply automatic improvements that don't require human approval."""
        actions = []

        # Apply high-confidence rule improvements
        for improvement in rule_improvements:
            if improvement["confidence"] > 0.9 and improvement["impact_score"] > 0.8:
                if self._apply_rule_improvement(improvement):
                    actions.append(f"Applied improvement to {improvement['rule_name']}")
                    self.improvements_applied += 1

        # Create high-confidence new rules
        for rule_suggestion in new_rules:
            if rule_suggestion["confidence"] > 0.9 and rule_suggestion["priority"] >= 4:
                if self._create_new_rule(rule_suggestion):
                    actions.append(f"Created new rule: {rule_suggestion['rule_name']}")
                    self.rules_generated += 1

        return actions

    def _apply_rule_improvement(self, improvement: dict[str, Any]) -> bool:
        """Apply a rule improvement."""
        try:
            from rule_validator import RuleAutoImprover

            improver = RuleAutoImprover(self.cursor_dir / "rules")
            rule_improvement = improver.improve_rule(improvement["rule_name"])

            if rule_improvement:
                # Save the improved rule
                improved_file = (
                    self.cursor_dir / "rules" / f"{improvement['rule_name']}.mdc"
                )
                with open(improved_file, "w") as f:
                    f.write(rule_improvement.improved_content)

                # Record the improvement
                improvement_record = {
                    "rule_name": improvement["rule_name"],
                    "improvement_type": rule_improvement.improvement_type,
                    "applied_at": datetime.now().isoformat(),
                    "confidence": rule_improvement.confidence,
                    "impact_score": rule_improvement.impact_score,
                }

                improvements_log = self.learning_dir / "applied_improvements.json"
                applied_improvements = []
                if improvements_log.exists():
                    with open(improvements_log) as f:
                        applied_improvements = json.load(f)

                applied_improvements.append(improvement_record)

                with open(improvements_log, "w") as f:
                    json.dump(applied_improvements, f, indent=2)

                return True

        except Exception as e:
            logging.error(f"Failed to apply rule improvement: {e}")

        return False

    def _create_new_rule(self, rule_suggestion: dict[str, Any]) -> bool:
        """Create a new rule from suggestion."""
        try:
            from auto_rule_generator import RuleGenerator

            generator = RuleGenerator(self.cursor_dir / "rules")
            rule_name = rule_suggestion["rule_name"]

            # Create a basic rule structure
            rule_content = f"""# {rule_name.replace('_', ' ').title()}

This rule was automatically generated based on detected patterns in the codebase.

## Description
{rule_suggestion["description"]}

## Pattern Type
{rule_suggestion["pattern_type"]}

## Impact
- **Confidence**: {rule_suggestion["confidence"]:.2f}
- **Priority**: {rule_suggestion["priority"]}/5
- **Affected Files**: {rule_suggestion["affected_files"]}

## Guidelines

Add specific guidelines here based on the detected patterns.

## Examples

Add practical examples of the pattern and how to address it.
"""

            # Create YAML frontmatter
            frontmatter = {
                "description": rule_suggestion["description"],
                "generated_by": "self_improvement_orchestrator",
                "pattern_type": rule_suggestion["pattern_type"],
                "confidence": rule_suggestion["confidence"],
                "priority": rule_suggestion["priority"],
                "alwaysApply": rule_suggestion["confidence"] > 0.9,
                "globs": ["**/*"],
            }

            # Format the rule
            lines = ["---"]
            for key, value in frontmatter.items():
                lines.append(f"{key}: {value}")
            lines.extend(["---", "", rule_content])

            # Save the rule
            rule_file = self.cursor_dir / "rules" / f"{rule_name}.mdc"
            with open(rule_file, "w") as f:
                f.write("\n".join(lines))

            # Record the creation
            creation_record = {
                "rule_name": rule_name,
                "created_at": datetime.now().isoformat(),
                "confidence": rule_suggestion["confidence"],
                "priority": rule_suggestion["priority"],
                "pattern_type": rule_suggestion["pattern_type"],
            }

            creations_log = self.learning_dir / "generated_rules.json"
            generated_rules = []
            if creations_log.exists():
                with open(creations_log) as f:
                    generated_rules = json.load(f)

            generated_rules.append(creation_record)

            with open(creations_log, "w") as f:
                json.dump(generated_rules, f, indent=2)

            return True

        except Exception as e:
            logging.error(f"Failed to create new rule: {e}")

        return False

    def _generate_recommendations(self, analysis_results: dict[str, Any]) -> list[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []

        # Health-based recommendations
        health = analysis_results["system_health"]
        if health.get("system_health") != "excellent":
            recommendations.append(
                "System health needs attention - review rule quality"
            )

        if health.get("average_score", 1.0) < 0.8:
            recommendations.append(
                "Rule quality is below target - consider comprehensive review"
            )

        # Improvement opportunities
        improvements = analysis_results["rule_improvements"]
        if improvements:
            recommendations.append(
                f"Apply {len(improvements)} pending rule improvements"
            )

        # New rule opportunities
        new_rules = analysis_results["new_rule_suggestions"]
        if new_rules:
            high_priority_rules = [r for r in new_rules if r["priority"] >= 4]
            if high_priority_rules:
                recommendations.append(
                    f"Create {len(high_priority_rules)} high-priority new rules"
                )

        # Learning insights
        insights = analysis_results["learning_insights"]
        if insights:
            recommendations.append(
                f"Review {len(insights)} learning insights for process improvements"
            )

        # Analytics-based recommendations
        analytics = analysis_results["analytics_summary"]
        if analytics.get("system_health") != "excellent":
            recommendations.append(
                "System performance needs optimization - check analytics"
            )

        return recommendations

    def get_system_status(self) -> dict[str, Any]:
        """Get current system status."""
        return {
            "last_analysis": self.last_analysis.isoformat(),
            "improvements_applied": self.improvements_applied,
            "rules_generated": self.rules_generated,
            "pending_improvements": len(self.hook_manager.get_pending_improvements()),
            "learning_insights": len(get_learning_insights()),
            "system_health": self._get_current_health(),
        }

    def _get_current_health(self) -> str:
        """Get current system health."""
        try:
            health_report = generate_health_report(
                str(self.cursor_dir / "rules"), str(self.analytics_dir)
            )
            return health_report.get("system_health", "unknown")
        except Exception:
            return "unknown"

    def trigger_continuous_improvement(self):
        """Trigger continuous improvement cycle."""
        # Check if enough time has passed since last analysis
        if datetime.now() - self.last_analysis > self.analysis_frequency:
            print("🔄 Continuous improvement cycle triggered...")
            self.run_full_analysis()

    def get_improvement_dashboard(self) -> dict[str, Any]:
        """Get dashboard data for improvement monitoring."""
        return {
            "system_status": self.get_system_status(),
            "recent_analytics": get_system_analytics(1),  # Last hour
            "pending_improvements": self.hook_manager.get_pending_improvements(),
            "learning_insights": get_learning_insights(),
            "health_trends": self._get_health_trends(),
        }

    def _get_health_trends(self) -> dict[str, Any]:
        """Get health trends over time."""
        trends = {"improving": [], "declining": [], "stable": []}

        # This would analyze historical health data
        # For now, return current assessment
        current_health = self._get_current_health()
        trends[current_health if current_health in trends else "stable"] = [
            "Current system health"
        ]

        return trends


def trigger_continuous_improvement():
    """Trigger the continuous improvement cycle."""
    cursor_dir = Path(".cursor")
    orchestrator = SelfImprovementOrchestrator(cursor_dir)
    orchestrator.trigger_continuous_improvement()


def run_full_improvement_analysis() -> dict[str, Any]:
    """Run a full improvement analysis and return results."""
    cursor_dir = Path(".cursor")
    orchestrator = SelfImprovementOrchestrator(cursor_dir)
    return orchestrator.run_full_analysis()


def get_improvement_dashboard() -> dict[str, Any]:
    """Get the improvement dashboard data."""
    cursor_dir = Path(".cursor")
    orchestrator = SelfImprovementOrchestrator(cursor_dir)
    return orchestrator.get_improvement_dashboard()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Self-improvement orchestrator")
    parser.add_argument(
        "--full-analysis", action="store_true", help="Run full improvement analysis"
    )
    parser.add_argument(
        "--dashboard", action="store_true", help="Get improvement dashboard"
    )
    parser.add_argument("--status", action="store_true", help="Get system status")
    parser.add_argument(
        "--auto-improve", action="store_true", help="Apply automatic improvements"
    )

    args = parser.parse_args()

    if args.full_analysis:
        print("🔄 Running full improvement analysis...")
        results = run_full_improvement_analysis()

        print("\n📊 Analysis Results:")
        print(
            f"   System Health: {results['system_health'].get('system_health', 'unknown')}"
        )
        print(f"   Rule Improvements: {len(results['rule_improvements'])}")
        print(f"   New Rules: {len(results['new_rule_suggestions'])}")
        print(f"   Learning Insights: {len(results['learning_insights'])}")
        print(f"   Actions Taken: {len(results['actions_taken'])}")

        if results["recommendations"]:
            print("\n💡 Recommendations:")
            for rec in results["recommendations"]:
                print(f"   • {rec}")

    elif args.dashboard:
        dashboard = get_improvement_dashboard()

        print("📊 Self-Improvement Dashboard")
        print("=" * 40)

        status = dashboard["system_status"]
        print("🏥 System Status:")
        print(f"   Last Analysis: {status['last_analysis']}")
        print(f"   Improvements Applied: {status['improvements_applied']}")
        print(f"   Rules Generated: {status['rules_generated']}")
        print(f"   System Health: {status['system_health']}")

        insights = dashboard["learning_insights"]
        if insights:
            print(f"\n💡 Learning Insights: {len(insights)}")
            for insight in insights[:3]:
                print(f"   • {insight['title']} ({insight['impact']})")

        trends = dashboard["health_trends"]
        print("\n📈 Health Trends:")
        for trend_type, items in trends.items():
            if items:
                print(f"   {trend_type.title()}: {len(items)} indicators")

    elif args.status:
        status = get_improvement_dashboard()["system_status"]
        print("🔍 System Status:")
        for key, value in status.items():
            print(f"   {key.replace('_', ' ').title()}: {value}")

    elif args.auto_improve:
        print("🚀 Applying automatic improvements...")
        results = run_full_improvement_analysis()

        actions = results["actions_taken"]
        if actions:
            print(f"✅ Applied {len(actions)} improvements:")
            for action in actions:
                print(f"   • {action}")
        else:
            print("ℹ️  No automatic improvements were applicable")

    else:
        print("Self-Improvement Orchestrator")
        print("Use --full-analysis to run comprehensive analysis")
        print("Use --dashboard to view improvement dashboard")
        print("Use --status to get system status")
        print("Use --auto-improve to apply automatic improvements")
