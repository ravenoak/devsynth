#!/usr/bin/env python3
"""
Validation script for DevSynth Cursor IDE rules configuration.

This script validates that the Cursor rules align with DevSynth's actual
project structure, tooling, and development patterns.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


def validate_project_structure() -> dict[str, Any]:
    """Validate that referenced directories and files exist."""
    results = {"status": "success", "issues": [], "checks": []}

    # Key directories that should exist
    expected_dirs = [
        "src/devsynth",
        "tests/unit",
        "tests/integration",
        "tests/behavior/features",
        "tests/behavior/steps",
        "tests/fixtures",
        "docs/specifications",
        "docs/policies",
        "docs/architecture",
        "scripts",
        "config",
    ]

    for dir_path in expected_dirs:
        full_path = Path(dir_path)
        if full_path.exists():
            results["checks"].append(f"✅ {dir_path} exists")
        else:
            results["issues"].append(f"❌ Missing directory: {dir_path}")
            results["status"] = "warning"

    # Key files that should exist
    expected_files = [
        "pyproject.toml",
        "Taskfile.yml",
        "CONTRIBUTING.md",  # Primary reference for Cursor IDE setup
        "tests/conftest.py",
        "tests/conftest_extensions.py",
        "src/devsynth/testing/run_tests.py",
    ]

    for file_path in expected_files:
        full_path = Path(file_path)
        if full_path.exists():
            results["checks"].append(f"✅ {file_path} exists")
        else:
            results["issues"].append(f"❌ Missing file: {file_path}")
            results["status"] = "warning"

    return results


def validate_poetry_configuration() -> dict[str, Any]:
    """Validate Poetry configuration matches rules expectations."""
    results = {"status": "success", "issues": [], "checks": []}

    try:
        # Check if Poetry is available
        result = subprocess.run(["poetry", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            results["checks"].append(f"✅ Poetry available: {result.stdout.strip()}")
        else:
            results["issues"].append("❌ Poetry not available")
            results["status"] = "error"
            return results
    except FileNotFoundError:
        results["issues"].append("❌ Poetry command not found")
        results["status"] = "error"
        return results

    # Check pyproject.toml structure
    pyproject_path = Path("pyproject.toml")
    if pyproject_path.exists():
        try:
            import toml

            config = toml.load(pyproject_path)

            # Check Python version constraint
            python_version = (
                config.get("tool", {})
                .get("poetry", {})
                .get("dependencies", {})
                .get("python")
            )
            if python_version and "3.12" in str(python_version):
                results["checks"].append("✅ Python 3.12 constraint found")
            else:
                results["issues"].append(
                    f"❌ Python 3.12 constraint not found: {python_version}"
                )
                results["status"] = "warning"

            # Check for key extras (in project.optional-dependencies)
            extras = config.get("project", {}).get("optional-dependencies", {})
            expected_extras = ["tests", "retrieval", "chromadb", "api", "minimal"]
            for extra in expected_extras:
                if extra in extras:
                    results["checks"].append(f"✅ Extra '{extra}' defined")
                else:
                    results["issues"].append(f"❌ Missing extra: {extra}")
                    results["status"] = "warning"

        except ImportError:
            results["issues"].append("❌ toml package not available for validation")
            results["status"] = "warning"
        except Exception as e:
            results["issues"].append(f"❌ Error reading pyproject.toml: {e}")
            results["status"] = "error"

    return results


def validate_testing_configuration() -> dict[str, Any]:
    """Validate testing configuration matches rules expectations."""
    results = {"status": "success", "issues": [], "checks": []}

    # Check for test marker verification script
    marker_script = Path("scripts/verify_test_markers.py")
    if marker_script.exists():
        results["checks"].append("✅ Test marker verification script exists")
    else:
        results["issues"].append("❌ Missing test marker verification script")
        results["status"] = "warning"

    # Check conftest configuration
    conftest_path = Path("tests/conftest.py")
    if conftest_path.exists():
        try:
            with open(conftest_path) as f:
                conftest_content = f.read()
                if "global_test_isolation" in conftest_content:
                    results["checks"].append("✅ Global test isolation fixture found")
                else:
                    results["issues"].append(
                        "❌ Global test isolation fixture not found"
                    )
                    results["status"] = "warning"
        except Exception as e:
            results["issues"].append(f"❌ Error reading conftest.py: {e}")
            results["status"] = "warning"

    # Check conftest_extensions
    extensions_path = Path("tests/conftest_extensions.py")
    if extensions_path.exists():
        results["checks"].append("✅ Test extensions configuration exists")
    else:
        results["issues"].append("❌ Missing test extensions configuration")
        results["status"] = "warning"

    return results


def validate_task_runner() -> dict[str, Any]:
    """Validate task runner configuration."""
    results = {"status": "success", "issues": [], "checks": []}

    # Check for Taskfile
    taskfile_path = Path("Taskfile.yml")
    if taskfile_path.exists():
        results["checks"].append("✅ Taskfile.yml exists")

        # Try to run task command
        try:
            result = subprocess.run(
                ["task", "--version"], capture_output=True, text=True
            )
            if result.returncode == 0:
                results["checks"].append(
                    f"✅ Task runner available: {result.stdout.strip()}"
                )
            else:
                results["issues"].append("❌ Task runner not available")
                results["status"] = "warning"
        except FileNotFoundError:
            results["issues"].append("❌ Task command not found")
            results["status"] = "warning"
    else:
        results["issues"].append("❌ Missing Taskfile.yml")
        results["status"] = "error"

    return results


def validate_security_audit() -> dict[str, Any]:
    """Validate security and audit configuration."""
    results = {"status": "success", "issues": [], "checks": []}

    # Check for dialectical audit script
    audit_script = Path("scripts/dialectical_audit.py")
    if audit_script.exists():
        results["checks"].append("✅ Dialectical audit script exists")
    else:
        results["issues"].append("❌ Missing dialectical audit script")
        results["status"] = "warning"

    # Check for security policy
    security_policy = Path("docs/policies/security.md")
    if security_policy.exists():
        results["checks"].append("✅ Security policy exists")
    else:
        results["issues"].append("❌ Missing security policy")
        results["status"] = "warning"

    # Check for dialectical audit policy
    dialectical_policy = Path("docs/policies/dialectical_audit.md")
    if dialectical_policy.exists():
        results["checks"].append("✅ Dialectical audit policy exists")
    else:
        results["issues"].append("❌ Missing dialectical audit policy")
        results["status"] = "warning"

    return results


def validate_cli_configuration() -> dict[str, Any]:
    """Validate CLI configuration matches rules expectations."""
    results = {"status": "success", "issues": [], "checks": []}

    # Check for CLI entry points
    cli_entry = Path("src/devsynth/cli.py")
    if cli_entry.exists():
        results["checks"].append("✅ CLI entry point exists")
    else:
        results["issues"].append("❌ Missing CLI entry point")
        results["status"] = "warning"

    # Check for Typer adapter
    typer_adapter = Path("src/devsynth/adapters/cli/typer_adapter.py")
    if typer_adapter.exists():
        results["checks"].append("✅ Typer adapter exists")
    else:
        results["issues"].append("❌ Missing Typer adapter")
        results["status"] = "warning"

    # Check for test runner
    test_runner = Path("src/devsynth/testing/run_tests.py")
    if test_runner.exists():
        results["checks"].append("✅ Test runner exists")
    else:
        results["issues"].append("❌ Missing test runner")
        results["status"] = "error"

    return results


def main():
    """Run all validation checks."""
    print("🔍 Validating DevSynth Cursor IDE Rules Configuration")
    print("=" * 60)

    validators = [
        ("Project Structure", validate_project_structure),
        ("Poetry Configuration", validate_poetry_configuration),
        ("Testing Configuration", validate_testing_configuration),
        ("Task Runner", validate_task_runner),
        ("Security & Audit", validate_security_audit),
        ("CLI Configuration", validate_cli_configuration),
    ]

    all_results = {}
    overall_status = "success"

    for name, validator in validators:
        print(f"\n📋 {name}")
        print("-" * 40)

        results = validator()
        all_results[name] = results

        for check in results["checks"]:
            print(f"  {check}")

        for issue in results["issues"]:
            print(f"  {issue}")

        if results["status"] != "success":
            if results["status"] == "error" or overall_status != "error":
                overall_status = results["status"]

    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)

    total_checks = sum(len(r["checks"]) for r in all_results.values())
    total_issues = sum(len(r["issues"]) for r in all_results.values())

    print(f"✅ Successful checks: {total_checks}")
    print(f"⚠️  Issues found: {total_issues}")
    print(f"🎯 Overall status: {overall_status.upper()}")

    if overall_status == "success":
        print("\n🎉 All validations passed! Cursor rules are properly configured.")
        return 0
    elif overall_status == "warning":
        print("\n⚠️  Some issues found, but configuration should work.")
        return 0
    else:
        print("\n❌ Critical issues found. Please address before using rules.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
