#!/usr/bin/env python3
"""
Main Self-Improvement System Interface

This script provides the main interface for interacting with the Cursor
self-improvement system, including activation, monitoring, and management.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

# Add hooks directory to path
sys.path.insert(0, ".cursor/hooks")


def run_activation():
    """Run the activation script."""
    try:
        from activate import main as activation_main

        return activation_main()
    except ImportError as e:
        print(f"❌ Activation script not available: {e}")
        return 1


def run_validation():
    """Run comprehensive validation."""
    try:
        from validate_self_improvement import main as validation_main

        return validation_main()
    except ImportError as e:
        print(f"❌ Validation script not available: {e}")
        return 1


def run_analysis():
    """Run full improvement analysis."""
    try:
        from self_improvement_orchestrator import run_full_improvement_analysis

        print("🔄 Running full improvement analysis...")
        results = run_full_improvement_analysis()

        print("\n📊 Analysis Complete:")
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

        return 0

    except ImportError as e:
        print(f"❌ Analysis tools not available: {e}")
        return 1


def show_dashboard():
    """Show improvement dashboard."""
    try:
        from self_improvement_orchestrator import get_improvement_dashboard

        dashboard = get_improvement_dashboard()

        print("📊 Self-Improvement Dashboard")
        print("=" * 50)

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

        return 0

    except ImportError as e:
        print(f"❌ Dashboard not available: {e}")
        return 1


def show_analytics(hours: int = 24):
    """Show system analytics."""
    try:
        from analytics_monitor import get_system_analytics

        analytics = get_system_analytics(hours)

        print(f"📈 System Analytics ({analytics['time_window']}):")
        print(f"   Rule Events: {analytics['recent_activity']['rule_events']}")
        print(f"   Command Events: {analytics['recent_activity']['command_events']}")
        print(f"   Unique Rules: {analytics['recent_activity']['unique_rules']}")
        print(f"   Success Rate: {analytics['recent_activity']['success_rate']:.2f}")
        print(f"   System Health: {analytics['system_health']}")

        print("\n🔥 Most Active Rules:")
        for rule, count in analytics["top_rules"][:5]:
            print(f"   {rule}: {count} uses")

        print("\n⚡ Most Active Commands:")
        for command, count in analytics["top_commands"][:5]:
            print(f"   {command}: {count} uses")

        return 0

    except ImportError as e:
        print(f"❌ Analytics not available: {e}")
        return 1


def validate_rules():
    """Validate all rules."""
    try:
        from rule_validator import generate_health_report, validate_all_rules

        print("🔍 Validating all rules...")
        results = validate_all_rules(".cursor/rules")

        valid_count = sum(1 for r in results.values() if r.is_valid)
        total_count = len(results)

        print(f"\n📊 Rule Validation Results:")
        print(f"   Valid Rules: {valid_count}/{total_count}")

        for rule_name, result in results.items():
            status = "✅" if result.is_valid else "❌"
            print(f"   {status} {rule_name}: {result.score:.2f}")

            if not result.is_valid and result.issues:
                print(f"      Issues: {result.issues[:2]}")

        # Generate health report
        print("\n📋 Generating health report...")
        health = generate_health_report(".cursor/rules", ".cursor/analytics")
        print(f"   System Health: {health['system_health']}")
        print(f"   Average Score: {health['average_score']:.2f}")
        return 0

    except ImportError as e:
        print(f"❌ Rule validation not available: {e}")
        return 1


def trigger_learning_event(event_type: str, context_key: str, context_value: str):
    """Trigger a learning event."""
    try:
        from pattern_learner import trigger_learning_event

        trigger_learning_event(event_type, {context_key: context_value})
        print(f"📝 Learning event recorded: {event_type}")
        return 0

    except ImportError as e:
        print(f"❌ Learning system not available: {e}")
        return 1


def get_system_status():
    """Get comprehensive system status."""
    try:
        # Check activation status
        status_file = Path(".cursor/learning/activation_status.json")
        if status_file.exists():
            with open(status_file) as f:
                activation_status = json.load(f)
        else:
            activation_status = {"activated": False}

        print("🔍 System Status:")
        print(f"   Activated: {activation_status.get('activated', False)}")
        print(f"   Version: {activation_status.get('version', 'unknown')}")

        # Check component availability
        components = [
            ("Hook Manager", "hook_manager"),
            ("Rule Generator", "auto_rule_generator"),
            ("Pattern Learner", "pattern_learner"),
            ("Rule Validator", "rule_validator"),
            ("Analytics Monitor", "analytics_monitor"),
            ("Self-Improvement Orchestrator", "self_improvement_orchestrator"),
        ]

        print("\n🔧 Components:")
        for name, module in components:
            try:
                __import__(module)
                print(f"   ✅ {name}")
            except ImportError:
                print(f"   ❌ {name}")

        # Check directories
        dirs_to_check = [
            "hooks",
            "analytics",
            "patterns",
            "learning",
            "suggestions",
            "logs",
        ]
        print("\n📁 Directories:")
        for dir_name in dirs_to_check:
            dir_path = Path(".cursor") / dir_name
            if dir_path.exists():
                print(f"   ✅ {dir_name}")
            else:
                print(f"   ❌ {dir_name}")

        return 0

    except Exception as e:
        print(f"❌ Error getting system status: {e}")
        return 1


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Cursor Self-Improvement System")
    parser.add_argument("--activate", action="store_true", help="Activate the system")
    parser.add_argument("--validate", action="store_true", help="Validate the system")
    parser.add_argument("--analysis", action="store_true", help="Run full analysis")
    parser.add_argument(
        "--dashboard", action="store_true", help="Show improvement dashboard"
    )
    parser.add_argument(
        "--analytics", type=int, default=24, help="Show analytics for N hours"
    )
    parser.add_argument(
        "--validate-rules", action="store_true", help="Validate all rules"
    )
    parser.add_argument("--status", action="store_true", help="Show system status")
    parser.add_argument(
        "--learn",
        nargs=3,
        metavar=("EVENT_TYPE", "CONTEXT_KEY", "CONTEXT_VALUE"),
        help="Record a learning event",
    )

    args = parser.parse_args()

    if args.activate:
        return run_activation()
    elif args.validate:
        return run_validation()
    elif args.analysis:
        return run_analysis()
    elif args.dashboard:
        return show_dashboard()
    elif args.analytics:
        return show_analytics(args.analytics)
    elif args.validate_rules:
        return validate_rules()
    elif args.status:
        return get_system_status()
    elif args.learn:
        return trigger_learning_event(*args.learn)
    else:
        print("Cursor Self-Improvement System")
        print("")
        print("Activation:")
        print("   --activate          Activate the self-improvement system")
        print("   --validate          Validate system setup and configuration")
        print("")
        print("Analysis & Monitoring:")
        print("   --analysis          Run comprehensive improvement analysis")
        print("   --dashboard         Show improvement dashboard")
        print("   --analytics <hours> Show system analytics (default: 24 hours)")
        print("   --validate-rules    Validate all Cursor rules")
        print("   --status            Show comprehensive system status")
        print("")
        print("Learning:")
        print("   --learn <event> <key> <value>  Record a learning event")
        print("")
        print("Examples:")
        print("   python .cursor/self_improvement.py --activate")
        print("   python .cursor/self_improvement.py --dashboard")
        print("   python .cursor/self_improvement.py --learn code_review security high")
        return 0


if __name__ == "__main__":
    sys.exit(main())
