#!/usr/bin/env python3
"""
Analytics and Monitoring System for Cursor Rules

Tracks rule usage, effectiveness, and performance metrics to enable
data-driven improvements to the rule system.
"""

import json
import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional


@dataclass
class RuleUsageEvent:
    """Represents a rule usage event."""

    rule_name: str
    event_type: str  # "applied", "loaded", "error", "ignored"
    timestamp: datetime
    context: dict[str, Any]
    success: bool
    confidence: float
    response_time: float  # milliseconds
    file_path: str | None = None
    error_message: str | None = None


@dataclass
class CommandUsageEvent:
    """Represents a command usage event."""

    command_name: str
    timestamp: datetime
    context: dict[str, Any]
    success: bool
    execution_time: float
    error_message: str | None = None


@dataclass
class SessionAnalytics:
    """Analytics for a development session."""

    session_id: str
    start_time: datetime
    end_time: datetime | None
    rules_used: list[str]
    commands_used: list[str]
    files_modified: list[str]
    errors_encountered: list[str]
    productivity_score: float
    context_switches: int


class RealTimeMetrics:
    """Real-time metrics collection."""

    def __init__(self):
        self.rule_usage: Deque[RuleUsageEvent] = deque(maxlen=1000)
        self.command_usage: Deque[CommandUsageEvent] = deque(maxlen=1000)
        self.session_start = datetime.now()
        self.lock = threading.Lock()

    def record_rule_usage(self, event: RuleUsageEvent):
        """Record a rule usage event."""
        with self.lock:
            self.rule_usage.append(event)

    def record_command_usage(self, event: CommandUsageEvent):
        """Record a command usage event."""
        with self.lock:
            self.command_usage.append(event)

    def get_recent_activity(self, minutes: int = 60) -> dict[str, Any]:
        """Get recent activity metrics."""
        cutoff = datetime.now() - timedelta(minutes=minutes)

        recent_rules = [e for e in self.rule_usage if e.timestamp > cutoff]
        recent_commands = [e for e in self.command_usage if e.timestamp > cutoff]

        return {
            "time_window": f"{minutes} minutes",
            "rule_events": len(recent_rules),
            "command_events": len(recent_commands),
            "unique_rules": len({e.rule_name for e in recent_rules}),
            "unique_commands": len({e.command_name for e in recent_commands}),
            "success_rate": self._calculate_success_rate(
                recent_rules + recent_commands
            ),
        }

    def _calculate_success_rate(self, events: list) -> float:
        """Calculate success rate for events."""
        if not events:
            return 0.0

        successful = sum(1 for e in events if getattr(e, "success", False))
        return successful / len(events)


class RuleAnalyticsCollector:
    """Collects and analyzes rule usage analytics."""

    def __init__(self, analytics_dir: Path):
        self.analytics_dir = analytics_dir
        self.analytics_dir.mkdir(parents=True, exist_ok=True)
        self.metrics = RealTimeMetrics()

    def record_rule_event(
        self,
        rule_name: str,
        event_type: str,
        context: dict[str, Any],
        success: bool = True,
        confidence: float = 1.0,
        response_time: float = 0.0,
        **kwargs,
    ):
        """Record a rule usage event."""
        event = RuleUsageEvent(
            rule_name=rule_name,
            event_type=event_type,
            timestamp=datetime.now(),
            context=context,
            success=success,
            confidence=confidence,
            response_time=response_time,
            **kwargs,
        )

        self.metrics.record_rule_usage(event)
        self._persist_rule_event(event)

    def record_command_event(
        self,
        command_name: str,
        context: dict[str, Any],
        success: bool = True,
        execution_time: float = 0.0,
        **kwargs,
    ):
        """Record a command usage event."""
        event = CommandUsageEvent(
            command_name=command_name,
            timestamp=datetime.now(),
            context=context,
            success=success,
            execution_time=execution_time,
            **kwargs,
        )

        self.metrics.record_command_usage(event)
        self._persist_command_event(event)

    def _persist_rule_event(self, event: RuleUsageEvent):
        """Persist rule event to storage."""
        day_key = event.timestamp.strftime("%Y-%m-%d")
        event_file = self.analytics_dir / f"rule_events_{day_key}.json"

        # Load existing events for the day
        events = []
        if event_file.exists():
            with open(event_file) as f:
                events = json.load(f)

        # Add new event
        events.append(asdict(event))

        # Save back to file
        with open(event_file, "w") as f:
            json.dump(events, f, indent=2, default=str)

    def _persist_command_event(self, event: CommandUsageEvent):
        """Persist command event to storage."""
        day_key = event.timestamp.strftime("%Y-%m-%d")
        event_file = self.analytics_dir / f"command_events_{day_key}.json"

        # Load existing events for the day
        events = []
        if event_file.exists():
            with open(event_file) as f:
                events = json.load(f)

        # Add new event
        events.append(asdict(event))

        # Save back to file
        with open(event_file, "w") as f:
            json.dump(events, f, indent=2, default=str)

    def generate_rule_analytics(self, rule_name: str, days: int = 7) -> dict[str, Any]:
        """Generate comprehensive analytics for a specific rule."""
        analytics = {
            "rule_name": rule_name,
            "analysis_period": f"{days} days",
            "usage_count": 0,
            "successful_applications": 0,
            "error_count": 0,
            "average_confidence": 0.0,
            "average_response_time": 0.0,
            "usage_trend": "stable",
            "peak_usage_hours": [],
            "common_contexts": [],
            "error_patterns": [],
            "improvement_suggestions": [],
        }

        # Collect data from recent days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        daily_usage = []
        total_usage = 0

        for day_offset in range(days):
            day = end_date - timedelta(days=day_offset)
            day_key = day.strftime("%Y-%m-%d")
            event_file = self.analytics_dir / f"rule_events_{day_key}.json"

            if event_file.exists():
                with open(event_file) as f:
                    events = json.load(f)

                day_events = [e for e in events if e["rule_name"] == rule_name]
                day_usage = len(day_events)
                daily_usage.append(day_usage)
                total_usage += day_usage

                for event in day_events:
                    if event["success"]:
                        analytics["successful_applications"] += 1
                    else:
                        analytics["error_count"] += 1

                    analytics["average_confidence"] += event.get("confidence", 1.0)
                    analytics["average_response_time"] += event.get(
                        "response_time", 0.0
                    )

        analytics["usage_count"] = total_usage

        if total_usage > 0:
            analytics["average_confidence"] /= total_usage
            analytics["average_response_time"] /= total_usage

        # Calculate trend
        analytics["usage_trend"] = self._calculate_trend(daily_usage)

        # Generate improvement suggestions
        analytics["improvement_suggestions"] = self._generate_improvement_suggestions(
            analytics
        )

        return analytics

    def _calculate_trend(self, daily_usage: list[int]) -> str:
        """Calculate usage trend from daily data."""
        if len(daily_usage) < 3:
            return "insufficient_data"

        # Compare recent vs older usage
        mid_point = len(daily_usage) // 2
        recent_avg = sum(daily_usage[:mid_point]) / mid_point
        older_avg = sum(daily_usage[mid_point:]) / (len(daily_usage) - mid_point)

        if recent_avg > older_avg * 1.2:
            return "increasing"
        elif recent_avg < older_avg * 0.8:
            return "decreasing"
        else:
            return "stable"

    def _generate_improvement_suggestions(self, analytics: dict[str, Any]) -> list[str]:
        """Generate improvement suggestions based on analytics."""
        suggestions = []

        if analytics["error_count"] / max(analytics["usage_count"], 1) > 0.1:
            suggestions.append("High error rate - consider clarifying rule language")

        if analytics["average_response_time"] > 1000:  # 1 second
            suggestions.append(
                "Slow response time - consider optimizing rule complexity"
            )

        if analytics["average_confidence"] < 0.7:
            suggestions.append(
                "Low confidence scores - consider adding more specific guidance"
            )

        if analytics["usage_trend"] == "decreasing":
            suggestions.append("Decreasing usage - consider if rule is still relevant")

        return suggestions

    def get_system_overview(self, hours: int = 24) -> dict[str, Any]:
        """Get system overview metrics."""
        recent_activity = self.metrics.get_recent_activity(hours)

        # Get rule popularity
        rule_usage_count = defaultdict(int)
        for event in self.metrics.rule_usage:
            if event.timestamp > datetime.now() - timedelta(hours=hours):
                rule_usage_count[event.rule_name] += 1

        # Get command popularity
        command_usage_count = defaultdict(int)
        for event in self.metrics.command_usage:
            if event.timestamp > datetime.now() - timedelta(hours=hours):
                command_usage_count[event.command_name] += 1

        return {
            "time_window": f"{hours} hours",
            "recent_activity": recent_activity,
            "top_rules": sorted(
                rule_usage_count.items(), key=lambda x: x[1], reverse=True
            )[:10],
            "top_commands": sorted(
                command_usage_count.items(), key=lambda x: x[1], reverse=True
            )[:10],
            "system_health": self._assess_system_health(),
        }

    def _assess_system_health(self) -> str:
        """Assess overall system health."""
        recent_activity = self.metrics.get_recent_activity(1)  # Last hour

        if recent_activity["success_rate"] > 0.9:
            return "excellent"
        elif recent_activity["success_rate"] > 0.7:
            return "good"
        elif recent_activity["success_rate"] > 0.5:
            return "fair"
        else:
            return "needs_attention"


class HookIntegration:
    """Integrates analytics into the hook system."""

    def __init__(self, analytics_dir: Path):
        self.collector = RuleAnalyticsCollector(analytics_dir)

    def on_rule_applied(
        self, rule_name: str, context: dict[str, Any], success: bool = True
    ):
        """Hook called when a rule is applied."""
        self.collector.record_rule_event(
            rule_name=rule_name, event_type="applied", context=context, success=success
        )

    def on_rule_error(
        self, rule_name: str, context: dict[str, Any], error_message: str
    ):
        """Hook called when a rule encounters an error."""
        self.collector.record_rule_event(
            rule_name=rule_name,
            event_type="error",
            context=context,
            success=False,
            error_message=error_message,
        )

    def on_command_executed(
        self,
        command_name: str,
        context: dict[str, Any],
        success: bool = True,
        execution_time: float = 0.0,
    ):
        """Hook called when a command is executed."""
        self.collector.record_command_event(
            command_name=command_name,
            context=context,
            success=success,
            execution_time=execution_time,
        )

    def get_analytics_summary(self) -> dict[str, Any]:
        """Get a summary of current analytics."""
        return self.collector.get_system_overview()


# Global analytics collector
_analytics_collector: RuleAnalyticsCollector | None = None


def get_analytics_collector() -> RuleAnalyticsCollector:
    """Get the global analytics collector."""
    global _analytics_collector
    if _analytics_collector is None:
        cursor_dir = Path(".cursor")
        _analytics_collector = RuleAnalyticsCollector(cursor_dir / "analytics")
    return _analytics_collector


def record_rule_usage(
    rule_name: str,
    event_type: str = "applied",
    context: dict[str, Any] = None,
    success: bool = True,
    **kwargs,
):
    """Record rule usage event."""
    collector = get_analytics_collector()
    collector.record_rule_event(
        rule_name=rule_name,
        event_type=event_type,
        context=context or {},
        success=success,
        **kwargs,
    )


def record_command_usage(
    command_name: str,
    context: dict[str, Any] = None,
    success: bool = True,
    execution_time: float = 0.0,
    **kwargs,
):
    """Record command usage event."""
    collector = get_analytics_collector()
    collector.record_command_event(
        command_name=command_name,
        context=context or {},
        success=success,
        execution_time=execution_time,
        **kwargs,
    )


def get_system_analytics(hours: int = 24) -> dict[str, Any]:
    """Get system analytics for the specified time window."""
    collector = get_analytics_collector()
    return collector.get_system_overview(hours)


def generate_rule_analytics(rule_name: str, days: int = 7) -> dict[str, Any]:
    """Generate detailed analytics for a specific rule."""
    collector = get_analytics_collector()
    return collector.generate_rule_analytics(rule_name, days)


# Integration functions for the hook manager
def integrate_analytics_hooks(hook_manager):
    """Integrate analytics collection into the hook system."""
    analytics = HookIntegration(Path(".cursor/analytics"))

    # Register analytics hooks
    hook_manager.register_hook(
        HookEvent.RULE_APPLIED,
        lambda ctx: analytics.on_rule_applied(ctx.rule_name, ctx.metadata or {}, True),
    )
    hook_manager.register_hook(
        HookEvent.ERROR_OCCURRED,
        lambda ctx: analytics.on_rule_error(
            ctx.rule_name, ctx.metadata or {}, ctx.error_message or ""
        ),
    )

    return analytics


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Rule analytics and monitoring")
    parser.add_argument(
        "--system-overview",
        type=int,
        default=24,
        help="Get system overview for N hours",
    )
    parser.add_argument("--rule-analytics", help="Get analytics for specific rule")
    parser.add_argument(
        "--generate-report",
        action="store_true",
        help="Generate comprehensive analytics report",
    )

    args = parser.parse_args()

    if args.system_overview:
        overview = get_system_analytics(args.system_overview)
        print(f"📊 System Overview ({overview['time_window']}):")
        print(f"   Rule Events: {overview['recent_activity']['rule_events']}")
        print(f"   Command Events: {overview['recent_activity']['command_events']}")
        print(f"   Unique Rules: {overview['recent_activity']['unique_rules']}")
        print(f"   Success Rate: {overview['recent_activity']['success_rate']:.2f}")
        print(f"   System Health: {overview['system_health']}")

        print("\n🔥 Top Rules:")
        for rule, count in overview["top_rules"][:5]:
            print(f"   {rule}: {count} uses")

        print("\n⚡ Top Commands:")
        for command, count in overview["top_commands"][:5]:
            print(f"   {command}: {count} uses")

    elif args.rule_analytics:
        analytics = generate_rule_analytics(args.rule_analytics)
        print(f"📈 Analytics for {args.rule_analytics}:")
        print(f"   Usage Count: {analytics['usage_count']}")
        print(
            f"   Success Rate: {analytics['successful_applications']/max(analytics['usage_count'],1):.2f}"
        )
        print(f"   Average Confidence: {analytics['average_confidence']:.2f}")
        print(f"   Trend: {analytics['usage_trend']}")

        if analytics["improvement_suggestions"]:
            print("\n💡 Improvement Suggestions:")
            for suggestion in analytics["improvement_suggestions"]:
                print(f"   • {suggestion}")

    elif args.generate_report:
        print("📋 Generating comprehensive analytics report...")

        # System overview
        overview = get_system_analytics(24)
        print("\n🏥 System Health Report:")
        print(f"   Health: {overview['system_health']}")
        print(f"   Success Rate: {overview['recent_activity']['success_rate']:.2f}")

        # Individual rule analytics
        cursor_dir = Path(".cursor")
        for rule_file in (cursor_dir / "rules").glob("*.mdc"):
            rule_name = rule_file.stem
            analytics = generate_rule_analytics(rule_name, 1)  # Last day

            if analytics["usage_count"] > 0:
                print(f"\n📊 {rule_name}:")
                print(f"   Usage: {analytics['usage_count']}")
                print(
                    f"   Effectiveness: {analytics['successful_applications']/analytics['usage_count']:.2f}"
                )
                print(f"   Trend: {analytics['usage_trend']}")

    else:
        print("Rule Analytics System")
        print("Use --system-overview <hours> to get system overview")
        print("Use --rule-analytics <rule_name> to get rule-specific analytics")
        print("Use --generate-report to generate comprehensive report")
