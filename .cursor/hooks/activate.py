#!/usr/bin/env python3
"""
Cursor Self-Improvement System Activation

This script activates the comprehensive self-improvement system for Cursor IDE,
integrating hooks, analytics, learning, and automated improvement capabilities.

Usage:
    python .cursor/hooks/activate.py --full-setup
    python .cursor/hooks/activate.py --quick-analysis
    python .cursor/hooks/activate.py --status
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(".cursor/logs/self_improvement.log"),
    ],
)

logger = logging.getLogger(__name__)


def load_config() -> dict[str, Any]:
    """Load self-improvement configuration."""
    config_file = Path(".cursor/hooks/config.json")
    if config_file.exists():
        with open(config_file) as f:
            return json.load(f)
    else:
        # Default configuration
        return {
            "self_improvement": {"enabled": True},
            "hooks": {
                "enabled_events": ["rule_loaded", "rule_applied", "command_executed"]
            },
            "analytics": {"collection_enabled": True},
        }


def check_prerequisites() -> bool:
    """Check that all prerequisites are met."""
    logger.info("🔍 Checking prerequisites...")

    issues = []

    # Check if .cursor directory exists
    cursor_dir = Path(".cursor")
    if not cursor_dir.exists():
        issues.append(".cursor directory not found")

    # Check if rules directory exists
    rules_dir = cursor_dir / "rules"
    if not rules_dir.exists():
        issues.append("Rules directory not found")

    # Check if hooks directory exists
    hooks_dir = cursor_dir / "hooks"
    if not hooks_dir.exists():
        issues.append("Hooks directory not found")

    # Check Python version
    if sys.version_info < (3, 8):
        issues.append("Python 3.8 or higher required")

    if issues:
        logger.error("❌ Prerequisites not met:")
        for issue in issues:
            logger.error(f"   - {issue}")
        return False

    logger.info("✅ All prerequisites met")
    return True


def setup_directories():
    """Set up required directories."""
    logger.info("📁 Setting up directories...")

    dirs_to_create = [
        ".cursor/hooks",
        ".cursor/analytics",
        ".cursor/patterns",
        ".cursor/learning",
        ".cursor/suggestions",
        ".cursor/logs",
    ]

    for dir_path in dirs_to_create:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        logger.info(f"   Created: {dir_path}")


def install_hook_integrations():
    """Install hook integrations into the main hook manager."""
    logger.info("🔗 Installing hook integrations...")

    try:
        # Import and set up the main hook manager
        from analytics_monitor import integrate_analytics_hooks
        from hook_manager import get_hook_manager

        hook_manager = get_hook_manager()
        analytics = integrate_analytics_hooks(hook_manager)

        logger.info("   ✅ Hook manager initialized")
        logger.info("   ✅ Analytics integration active")

        # Save integration status
        status_file = Path(".cursor/learning/integration_status.json")
        status = {
            "hooks_integrated": True,
            "analytics_enabled": True,
            "integration_timestamp": (
                Path(".cursor").stat().st_mtime if Path(".cursor").exists() else 0
            ),
            "last_check": (
                Path(".cursor/hooks").stat().st_mtime
                if Path(".cursor/hooks").exists()
                else 0
            ),
        }

        with open(status_file, "w") as f:
            json.dump(status, f, indent=2)

        return True

    except Exception as e:
        logger.error(f"❌ Failed to install hook integrations: {e}")
        return False


def run_initial_analysis():
    """Run initial analysis to establish baseline."""
    logger.info("📊 Running initial analysis...")

    try:
        from self_improvement_orchestrator import run_full_improvement_analysis

        results = run_full_improvement_analysis()

        logger.info("   ✅ Initial analysis complete")
        logger.info(
            f"   📊 System Health: {results['system_health'].get('system_health', 'unknown')}"
        )
        logger.info(f"   🔧 Rule Improvements: {len(results['rule_improvements'])}")
        logger.info(f"   💡 New Rules: {len(results['new_rule_suggestions'])}")

        return True

    except Exception as e:
        logger.error(f"❌ Initial analysis failed: {e}")
        return False


def setup_continuous_improvement():
    """Set up continuous improvement monitoring."""
    logger.info("🔄 Setting up continuous improvement...")

    try:
        # Create a simple monitoring script
        monitor_script = """
#!/usr/bin/env python3
# Continuous improvement monitor
import time
from pathlib import Path

def check_and_improve():
    try:
        from self_improvement_orchestrator import trigger_continuous_improvement
        trigger_continuous_improvement()
        print("✅ Continuous improvement check completed")
    except Exception as e:
        print(f"❌ Continuous improvement failed: {e}")

if __name__ == "__main__":
    while True:
        check_and_improve()
        time.sleep(3600)  # Check every hour
"""

        monitor_file = Path(".cursor/hooks/continuous_monitor.py")
        with open(monitor_file, "w") as f:
            f.write(monitor_script)

        logger.info("   ✅ Continuous monitoring script created")

        # Create activation status
        status_file = Path(".cursor/learning/activation_status.json")
        status = {
            "activated": True,
            "activation_timestamp": Path(".cursor/hooks").stat().st_mtime,
            "continuous_monitoring": True,
            "auto_improvement": True,
            "version": "1.0.0",
        }

        with open(status_file, "w") as f:
            json.dump(status, f, indent=2)

        return True

    except Exception as e:
        logger.error(f"❌ Failed to setup continuous improvement: {e}")
        return False


def full_setup():
    """Perform full setup of the self-improvement system."""
    logger.info("🚀 Starting full self-improvement system setup...")

    if not check_prerequisites():
        return False

    setup_directories()

    if not install_hook_integrations():
        return False

    if not run_initial_analysis():
        logger.warning("⚠️  Initial analysis failed, but setup continuing...")

    if not setup_continuous_improvement():
        return False

    logger.info("🎉 Self-improvement system fully activated!")
    logger.info("")
    logger.info("📋 Next Steps:")
    logger.info("   1. Restart Cursor IDE to activate hooks")
    logger.info("   2. Use /expand-phase, /refine-phase commands to test integration")
    logger.info("   3. Check .cursor/learning/ for improvement suggestions")
    logger.info("   4. Monitor .cursor/analytics/ for usage statistics")
    logger.info("")
    logger.info("🔧 Management Commands:")
    logger.info("   python .cursor/hooks/self_improvement_orchestrator.py --dashboard")
    logger.info("   python .cursor/hooks/rule_validator.py --health-report")
    logger.info("   python .cursor/hooks/analytics_monitor.py --system-overview 24")

    return True


def quick_analysis():
    """Run a quick analysis of the current state."""
    logger.info("⚡ Running quick analysis...")

    try:
        from self_improvement_orchestrator import get_improvement_dashboard

        dashboard = get_improvement_dashboard()

        logger.info("📊 Quick Analysis Results:")
        logger.info(f"   System Health: {dashboard['system_status']['system_health']}")
        logger.info(
            f"   Improvements Applied: {dashboard['system_status']['improvements_applied']}"
        )
        logger.info(
            f"   Rules Generated: {dashboard['system_status']['rules_generated']}"
        )
        logger.info(f"   Learning Insights: {len(dashboard['learning_insights'])}")

        return True

    except Exception as e:
        logger.error(f"❌ Quick analysis failed: {e}")
        return False


def get_status():
    """Get current activation status."""
    status_file = Path(".cursor/learning/activation_status.json")

    if status_file.exists():
        with open(status_file) as f:
            status = json.load(f)

        logger.info("🔍 Current Status:")
        logger.info(f"   Activated: {status.get('activated', False)}")
        logger.info(f"   Version: {status.get('version', 'unknown')}")
        logger.info(
            f"   Continuous Monitoring: {status.get('continuous_monitoring', False)}"
        )
        logger.info(
            f"   Last Activation: {status.get('activation_timestamp', 'unknown')}"
        )

        return status.get("activated", False)

    else:
        logger.info("ℹ️  Self-improvement system not yet activated")
        return False


def main():
    """Main activation function."""
    import argparse

    parser = argparse.ArgumentParser(description="Cursor Self-Improvement System")
    parser.add_argument(
        "--full-setup", action="store_true", help="Complete setup and activation"
    )
    parser.add_argument(
        "--quick-analysis", action="store_true", help="Quick status analysis"
    )
    parser.add_argument("--status", action="store_true", help="Show activation status")
    parser.add_argument(
        "--validate", action="store_true", help="Validate current setup"
    )

    args = parser.parse_args()

    if args.full_setup:
        success = full_setup()
        return 0 if success else 1

    elif args.quick_analysis:
        success = quick_analysis()
        return 0 if success else 1

    elif args.status:
        activated = get_status()
        return 0 if activated else 1

    elif args.validate:
        logger.info("🔍 Validating setup...")
        if check_prerequisites():
            logger.info("✅ Prerequisites met")
            if get_status():
                logger.info("✅ System activated")
                quick_analysis()
                return 0
            else:
                logger.error("❌ System not activated")
                return 1
        else:
            logger.error("❌ Prerequisites not met")
            return 1

    else:
        print("Cursor Self-Improvement System")
        print("Use --full-setup for complete activation")
        print("Use --quick-analysis for status check")
        print("Use --status for activation status")
        print("Use --validate for comprehensive validation")
        return 0


if __name__ == "__main__":
    sys.exit(main())
