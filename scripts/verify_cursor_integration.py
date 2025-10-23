#!/usr/bin/env python3
"""
Verify Cursor IDE integration setup and configuration.

This script validates that the Cursor IDE integration is properly configured
and all required files are present and correctly structured.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def check_cursor_directory_structure() -> Tuple[bool, List[str]]:
    """Check that .cursor directory structure is correct."""
    issues = []
    cursor_dir = Path('.cursor')

    if not cursor_dir.exists():
        issues.append("❌ .cursor directory not found")
        return False, issues

    if not cursor_dir.is_dir():
        issues.append("❌ .cursor is not a directory")
        return False, issues

    # Check required subdirectories
    rules_dir = cursor_dir / 'rules'
    commands_dir = cursor_dir / 'commands'

    if not rules_dir.exists():
        issues.append("❌ .cursor/rules directory not found")
    elif not rules_dir.is_dir():
        issues.append("❌ .cursor/rules is not a directory")

    if not commands_dir.exists():
        issues.append("❌ .cursor/commands directory not found")
    elif not commands_dir.is_dir():
        issues.append("❌ .cursor/commands is not a directory")

    # Check for README
    readme_file = cursor_dir / 'README.md'
    if not readme_file.exists():
        issues.append("❌ .cursor/README.md not found")
    elif not readme_file.is_file():
        issues.append("❌ .cursor/README.md is not a file")

    return len(issues) == 0, issues


def check_cursor_rules() -> Tuple[bool, List[str]]:
    """Check that required Cursor rules are present and properly formatted."""
    issues = []
    rules_dir = Path('.cursor/rules')

    if not rules_dir.exists():
        return True, []  # Skip if rules directory doesn't exist

    # Core rules that should always apply (philosophy and methodology)
    core_always_apply_rules = [
        '00-architecture.mdc',
        '00-project-core.md',
        '01-edrr-framework.mdc',
        '02-specification-driven.mdc'
    ]

    # Context-specific rules that should not always apply
    context_specific_rules = [
        '01-testing-standards.md',
        '02-bdd-workflow.md',
        '03-security-compliance.md',
        '03-testing-philosophy.mdc',
        '04-code-style.md',
        '04-security-compliance.mdc',
        '05-dialectical-reasoning.mdc',
        '05-documentation.md',
        '06-commit-workflow.md',
        '07-cursor-rules-management.md',
        '07-poetry-environment.md'
    ]

    required_rules = core_always_apply_rules + context_specific_rules

    for rule in required_rules:
        rule_file = rules_dir / rule
        if not rule_file.exists():
            issues.append(f"❌ Required rule not found: {rule}")
        elif not rule_file.is_file():
            issues.append(f"❌ Rule is not a file: {rule}")
        else:
            # Check for YAML frontmatter
            content = rule_file.read_text()
            if not content.startswith('---'):
                issues.append(f"❌ Rule missing YAML frontmatter: {rule}")
            elif 'description:' not in content:
                issues.append(f"❌ Rule missing description in frontmatter: {rule}")

            # Check alwaysApply in YAML frontmatter only
            import re

            # Extract YAML frontmatter (between --- markers)
            frontmatter_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
            if frontmatter_match:
                frontmatter = frontmatter_match.group(1)
                if rule in core_always_apply_rules:
                    if 'alwaysApply: true' not in frontmatter:
                        issues.append(f"❌ Core rule should have alwaysApply: true: {rule}")
                elif rule in context_specific_rules:
                    if 'alwaysApply: true' in frontmatter:
                        issues.append(f"❌ Context-specific rule should not have alwaysApply: true: {rule}")
                    elif 'alwaysApply:' not in frontmatter:
                        issues.append(f"❌ Context-specific rule should have alwaysApply: false: {rule}")
            else:
                issues.append(f"❌ Rule missing proper YAML frontmatter format: {rule}")

    return len(issues) == 0, issues


def check_cursor_commands() -> Tuple[bool, List[str]]:
    """Check that required Cursor commands are present."""
    issues = []
    commands_dir = Path('.cursor/commands')

    if not commands_dir.exists():
        return True, []  # Skip if commands directory doesn't exist

    required_commands = [
        'expand-phase.md',
        'differentiate-phase.md',
        'refine-phase.md',
        'retrospect-phase.md',
        'generate-specification.md',
        'validate-bdd-scenarios.md',
        'generate-test-suite.md',
        'code-review.md'
    ]

    for command in required_commands:
        command_file = commands_dir / command
        if not command_file.exists():
            issues.append(f"❌ Required command not found: {command}")
        elif not command_file.is_file():
            issues.append(f"❌ Command is not a file: {command}")

    return len(issues) == 0, issues


def check_project_configuration() -> Tuple[bool, List[str]]:
    """Check that project configuration includes Cursor integration."""
    issues = []

    # Check .devsynth/project.yaml
    project_config = Path('.devsynth/project.yaml')
    if project_config.exists():
        try:
            import yaml
            with open(project_config) as f:
                config = yaml.safe_load(f)

            cursor_integration = config.get('cursor_integration', {})
            if not cursor_integration.get('enabled', False):
                issues.append("❌ Cursor integration not enabled in project.yaml")

            # Check development workflow configuration
            dev_workflow = config.get('development_workflow', {})
            edrr_framework = dev_workflow.get('edrr_framework', {})
            if not edrr_framework.get('enabled', False):
                issues.append("❌ EDRR framework not enabled in project.yaml")
            if not edrr_framework.get('cursor_enhanced', False):
                issues.append("❌ EDRR cursor enhancement not enabled in project.yaml")

        except Exception as e:
            issues.append(f"❌ Error reading project.yaml: {e}")

    # Check config/default.yml
    config_file = Path('config/default.yml')
    if config_file.exists():
        try:
            import yaml
            with open(config_file) as f:
                config = yaml.safe_load(f)

            cursor_integration = config.get('cursor_integration', {})
            if not cursor_integration.get('enabled', False):
                issues.append("❌ Cursor integration not enabled in config/default.yml")

            dev_workflow = config.get('development_workflow', {})
            edrr_framework = dev_workflow.get('edrr_framework', {})
            if not edrr_framework.get('enabled', False):
                issues.append("❌ EDRR framework not enabled in config/default.yml")

        except Exception as e:
            issues.append(f"❌ Error reading config/default.yml: {e}")

    return len(issues) == 0, issues


def check_constitution() -> Tuple[bool, List[str]]:
    """Check that project constitution exists and is properly formatted."""
    issues = []

    constitution_file = Path('constitution.md')
    if not constitution_file.exists():
        issues.append("❌ constitution.md not found")
    elif not constitution_file.is_file():
        issues.append("❌ constitution.md is not a file")
    else:
        content = constitution_file.read_text()
        required_sections = [
            '# DevSynth Project Constitution',
            '## Technology Stack',
            '## Architectural Patterns',
            '## Coding Standards',
            '## Development Workflow'
        ]

        for section in required_sections:
            if section not in content:
                issues.append(f"❌ Missing required section in constitution: {section}")

    return len(issues) == 0, issues


def check_documentation() -> Tuple[bool, List[str]]:
    """Check that integration documentation exists."""
    issues = []

    # Check for Cursor integration guide
    docs_file = Path('docs/developer_guides/cursor_integration.md')
    if not docs_file.exists():
        issues.append("❌ Cursor integration documentation not found")
    elif not docs_file.is_file():
        issues.append("❌ Cursor integration documentation is not a file")

    # Check README mentions Cursor integration
    readme_file = Path('README.md')
    if readme_file.exists():
        content = readme_file.read_text()
        if 'Cursor IDE Integration' not in content:
            issues.append("❌ README.md does not mention Cursor IDE integration")

    return len(issues) == 0, issues


def check_agents_md() -> Tuple[bool, List[str]]:
    """Check that AGENTS.md includes Cursor integration guidance."""
    issues = []

    agents_file = Path('AGENTS.md')
    if not agents_file.exists():
        issues.append("❌ AGENTS.md not found")
    else:
        content = agents_file.read_text()
        if 'Cursor IDE Integration' not in content:
            issues.append("❌ AGENTS.md does not include Cursor IDE integration section")

        if '.cursor/' not in content:
            issues.append("❌ AGENTS.md does not reference .cursor directory structure")

    return len(issues) == 0, issues


def main():
    """Run all validation checks."""
    print("🔍 Verifying Cursor IDE Integration Setup")
    print("=" * 50)

    checks = [
        (check_cursor_directory_structure, "Cursor Directory Structure"),
        (check_cursor_rules, "Cursor Rules"),
        (check_cursor_commands, "Cursor Commands"),
        (check_project_configuration, "Project Configuration"),
        (check_constitution, "Project Constitution"),
        (check_documentation, "Documentation"),
        (check_agents_md, "AGENTS.md Integration")
    ]

    all_passed = True
    total_issues = 0

    for check_func, check_name in checks:
        print(f"\n📋 {check_name}")
        print("-" * 30)

        passed, issues = check_func()
        if passed:
            print("✅ PASSED")
        else:
            print("❌ FAILED")
            all_passed = False
            total_issues += len(issues)

            for issue in issues:
                print(f"   {issue}")

    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All checks passed! Cursor IDE integration is properly configured.")
        return 0
    else:
        print(f"⚠️  {total_issues} issues found. Please address them before using Cursor integration.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
