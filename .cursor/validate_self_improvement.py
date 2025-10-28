#!/usr/bin/env python3
"""
Comprehensive Validation of Cursor Self-Improvement System

This script validates that all components of the self-improvement system
are properly configured and functioning correctly.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def validate_directory_structure() -> tuple[bool, list[str]]:
    """Validate that all required directories exist."""
    issues = []
    required_dirs = [
        ".cursor",
        ".cursor/rules",
        ".cursor/commands",
        ".cursor/hooks",
        ".cursor/analytics",
        ".cursor/patterns",
        ".cursor/learning",
        ".cursor/suggestions",
        ".cursor/logs",
    ]

    for dir_path in required_dirs:
        dir_obj = Path(dir_path)
        if not dir_obj.exists():
            issues.append(f"❌ Directory not found: {dir_path}")
        elif not dir_obj.is_dir():
            issues.append(f"❌ {dir_path} is not a directory")
        else:
            # Check if directory is writable
            try:
                test_file = dir_obj / ".write_test"
                test_file.touch()
                test_file.unlink()
            except Exception:
                issues.append(f"❌ Directory not writable: {dir_path}")

    return len(issues) == 0, issues


def validate_required_files() -> tuple[bool, list[str]]:
    """Validate that all required files exist."""
    issues = []
    required_files = [
        ".cursor/README.md",
        ".cursor/modes.json",
        ".cursor/hooks/__init__.py",
        ".cursor/hooks/hook_manager.py",
        ".cursor/hooks/auto_rule_generator.py",
        ".cursor/hooks/pattern_learner.py",
        ".cursor/hooks/rule_validator.py",
        ".cursor/hooks/analytics_monitor.py",
        ".cursor/hooks/self_improvement_orchestrator.py",
        ".cursor/hooks/activate.py",
        ".cursor/hooks/config.json",
        "constitution.md",
    ]

    for file_path in required_files:
        file_obj = Path(file_path)
        if not file_obj.exists():
            issues.append(f"❌ File not found: {file_path}")
        elif not file_obj.is_file():
            issues.append(f"❌ {file_path} is not a file")

    return len(issues) == 0, issues


def validate_rules() -> tuple[bool, list[str]]:
    """Validate Cursor rules are properly formatted."""
    issues = []
    rules_dir = Path(".cursor/rules")

    if not rules_dir.exists():
        return True, []  # Skip if no rules directory

    # Check for core rules
    core_rules = [
        "00-architecture.mdc",
        "01-edrr-framework.mdc",
        "02-specification-driven.mdc",
        "03-testing-philosophy.mdc",
        "04-security-compliance.mdc",
        "05-dialectical-reasoning.mdc",
    ]

    for rule in core_rules:
        rule_file = rules_dir / rule
        if not rule_file.exists():
            issues.append(f"❌ Core rule not found: {rule}")
        else:
            # Validate YAML frontmatter
            content = rule_file.read_text()
            if not content.startswith("---"):
                issues.append(f"❌ Rule missing YAML frontmatter: {rule}")
            elif "description:" not in content:
                issues.append(f"❌ Rule missing description: {rule}")

    return len(issues) == 0, issues


def validate_commands() -> tuple[bool, list[str]]:
    """Validate Cursor commands are present."""
    issues = []
    commands_dir = Path(".cursor/commands")

    if not commands_dir.exists():
        return True, []  # Skip if no commands directory

    required_commands = [
        "expand-phase.md",
        "differentiate-phase.md",
        "refine-phase.md",
        "retrospect-phase.md",
        "generate-specification.md",
        "validate-bdd-scenarios.md",
    ]

    for command in required_commands:
        command_file = commands_dir / command
        if not command_file.exists():
            issues.append(f"❌ Command not found: {command}")

    return len(issues) == 0, issues


def validate_configuration() -> tuple[bool, list[str]]:
    """Validate configuration files."""
    issues = []

    # Check project configuration
    project_config = Path(".devsynth/project.yaml")
    if project_config.exists():
        try:
            import yaml

            with open(project_config) as f:
                config = yaml.safe_load(f)

            cursor_integration = config.get("cursor_integration", {})
            if not cursor_integration.get("enabled", False):
                issues.append("❌ Cursor integration not enabled in project.yaml")

        except Exception as e:
            issues.append(f"❌ Error reading project.yaml: {e}")

    # Check default configuration
    config_file = Path("config/default.yml")
    if config_file.exists():
        try:
            import yaml

            with open(config_file) as f:
                config = yaml.safe_load(f)

            cursor_integration = config.get("cursor_integration", {})
            if not cursor_integration.get("enabled", False):
                issues.append("❌ Cursor integration not enabled in config/default.yml")

            dev_workflow = config.get("development_workflow", {})
            edrr_framework = dev_workflow.get("edrr_framework", {})
            if not edrr_framework.get("enabled", False):
                issues.append("❌ EDRR framework not enabled in config/default.yml")

        except Exception as e:
            issues.append(f"❌ Error reading config/default.yml: {e}")

    # Check hooks configuration
    hooks_config = Path(".cursor/hooks/config.json")
    if hooks_config.exists():
        try:
            with open(hooks_config) as f:
                config = json.load(f)

            if not config.get("self_improvement", {}).get("enabled", False):
                issues.append("❌ Self-improvement not enabled in hooks config")

        except Exception as e:
            issues.append(f"❌ Error reading hooks config: {e}")

    return len(issues) == 0, issues


def validate_imports() -> tuple[bool, list[str]]:
    """Validate that all modules can be imported."""
    issues = []

    # Test hook manager import
    try:
        sys.path.insert(0, ".cursor/hooks")
        import analytics_monitor
        import auto_rule_generator
        import hook_manager
        import pattern_learner
        import rule_validator
        import self_improvement_orchestrator
    except ImportError as e:
        issues.append(f"❌ Import error in hooks modules: {e}")
    except Exception as e:
        issues.append(f"❌ Error loading hooks modules: {e}")
    finally:
        if ".cursor/hooks" in sys.path:
            sys.path.remove(".cursor/hooks")

    return len(issues) == 0, issues


def validate_system_integration() -> tuple[bool, list[str]]:
    """Validate system integration points."""
    issues = []

    # Check if hook manager can be initialized
    try:
        sys.path.insert(0, ".cursor/hooks")
        from hook_manager import get_hook_manager

        hook_manager = get_hook_manager()
        pending_improvements = hook_manager.get_pending_improvements()

        # This should not crash
        assert isinstance(pending_improvements, list)

    except Exception as e:
        issues.append(f"❌ Hook manager initialization failed: {e}")
    finally:
        if ".cursor/hooks" in sys.path:
            sys.path.remove(".cursor/hooks")

    # Check if learning engine works
    try:
        sys.path.insert(0, ".cursor/hooks")
        from pattern_learner import get_learning_insights

        insights = get_learning_insights()
        assert isinstance(insights, list)

    except Exception as e:
        issues.append(f"❌ Learning engine initialization failed: {e}")
    finally:
        if ".cursor/hooks" in sys.path:
            sys.path.remove(".cursor/hooks")

    return len(issues) == 0, issues


def validate_analytics() -> tuple[bool, list[str]]:
    """Validate analytics system."""
    issues = []
    analytics_dir = Path(".cursor/analytics")

    if not analytics_dir.exists():
        issues.append("❌ Analytics directory not found")
        return False, issues

    # Check if we can write analytics
    try:
        test_file = analytics_dir / "test_write.json"
        test_data = {"test": "data", "timestamp": "test"}
        with open(test_file, "w") as f:
            json.dump(test_data, f)
        test_file.unlink()
    except Exception as e:
        issues.append(f"❌ Analytics directory not writable: {e}")

    return len(issues) == 0, issues


def validate_learning_system() -> tuple[bool, list[str]]:
    """Validate learning system."""
    issues = []
    learning_dir = Path(".cursor/learning")

    if not learning_dir.exists():
        issues.append("❌ Learning directory not found")
        return False, issues

    # Check if we can create learning artifacts
    try:
        test_insight = learning_dir / "test_insight.json"
        test_data = {
            "insight_id": "test",
            "title": "Test Insight",
            "confidence": 0.8,
            "created_at": "2025-01-01T00:00:00",
        }
        with open(test_insight, "w") as f:
            json.dump(test_data, f)
        test_insight.unlink()
    except Exception as e:
        issues.append(f"❌ Learning directory not writable: {e}")

    return len(issues) == 0, issues


def run_functional_tests() -> tuple[bool, list[str]]:
    """Run basic functional tests."""
    issues = []

    try:
        # Test rule validation
        sys.path.insert(0, ".cursor/hooks")
        from rule_validator import validate_all_rules

        rules_dir = ".cursor/rules"
        if Path(rules_dir).exists():
            results = validate_all_rules(rules_dir)
            valid_rules = sum(1 for r in results.values() if r.is_valid)

            if valid_rules == 0:
                issues.append("❌ No valid rules found")
            else:
                issues.append(f"✅ {valid_rules}/{len(results)} rules are valid")

        # Test analytics
        from analytics_monitor import get_system_analytics

        try:
            analytics = get_system_analytics(1)  # Last hour
            issues.append(
                f"✅ Analytics system active: {analytics['recent_activity']['rule_events']} events"
            )
        except Exception:
            issues.append("❌ Analytics system not responding")

    except ImportError as e:
        issues.append(f"❌ Import error: {e}")
    except Exception as e:
        issues.append(f"❌ Functional test failed: {e}")
    finally:
        if ".cursor/hooks" in sys.path:
            sys.path.remove(".cursor/hooks")

    return len([i for i in issues if i.startswith("❌")]) == 0, issues


def main():
    """Run comprehensive validation."""
    print("🔍 Comprehensive Self-Improvement System Validation")
    print("=" * 60)

    validation_checks = [
        (validate_directory_structure, "Directory Structure"),
        (validate_required_files, "Required Files"),
        (validate_rules, "Cursor Rules"),
        (validate_commands, "Cursor Commands"),
        (validate_configuration, "Configuration"),
        (validate_imports, "Module Imports"),
        (validate_system_integration, "System Integration"),
        (validate_analytics, "Analytics System"),
        (validate_learning_system, "Learning System"),
        (run_functional_tests, "Functional Tests"),
    ]

    all_passed = True
    total_issues = 0

    for check_func, check_name in validation_checks:
        print(f"\n📋 {check_name}")
        print("-" * 40)

        try:
            passed, issues = check_func()

            if passed:
                print("✅ PASSED")
                if issues:  # Some checks return info messages
                    for issue in issues:
                        if not issue.startswith("❌"):
                            print(f"   {issue}")
            else:
                print("❌ FAILED")
                all_passed = False
                total_issues += len([i for i in issues if i.startswith("❌")])

                for issue in issues:
                    print(f"   {issue}")

        except Exception as e:
            print(f"❌ ERROR: {e}")
            all_passed = False
            total_issues += 1

    print("\n" + "=" * 60)

    if all_passed:
        print("🎉 All validation checks passed!")
        print("✅ Self-improvement system is properly configured and ready for use.")
        print("")
        print("🚀 Next Steps:")
        print("   1. Run: python .cursor/hooks/activate.py --full-setup")
        print("   2. Test: Use EDRR commands in Cursor IDE")
        print("   3. Monitor: Check .cursor/learning/ for insights")
        print(
            "   4. Analyze: Run python .cursor/hooks/self_improvement_orchestrator.py --dashboard"
        )
        return 0
    else:
        print(f"⚠️  {total_issues} issues found.")
        print("❌ Please address the issues before using the self-improvement system.")
        print("")
        print("🔧 Troubleshooting:")
        print("   1. Run: python .cursor/validate_self_improvement.py --validate")
        print("   2. Check: .cursor/logs/self_improvement.log for errors")
        print("   3. Verify: All required directories and files exist")
        return 1


if __name__ == "__main__":
    sys.exit(main())
