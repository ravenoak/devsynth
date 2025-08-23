#!/usr/bin/env python3
"""
Script to verify test organization standards.

This script checks that:
1. All test directories have __init__.py files
2. Test files follow the standard naming patterns
3. Test files are in the correct directories
4. No test classes have __init__ constructors (they should use pytest fixtures)

Usage:
    python tests/verify_test_organization.py
"""

import ast
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Define the root directory of the project
PROJECT_ROOT = Path(__file__).parent.parent
TESTS_ROOT = PROJECT_ROOT / "tests"

# Files that serve as sentinels and should always be present
SENTINEL_TEST_FILES = [
    TESTS_ROOT / "tmp_speed_dummy.py",
]

# Define standard patterns
UNIT_TEST_PATTERN = re.compile(r"tests/unit/.*?/test_[a-z0-9_]+\.py$")
INTEGRATION_TEST_PATTERN = re.compile(r"tests/integration/.*?/test_[a-z0-9_]+\.py$")
BEHAVIOR_FEATURE_PATTERN = re.compile(
    r"tests/behavior/features(?:/[a-z0-9_]+)*/[a-z0-9_]+\.feature$"
)
BEHAVIOR_STEPS_PATTERN = re.compile(
    r"tests/behavior/steps/(?:test_)?[a-z0-9_]+_steps\.py$"
)


def check_init_files() -> List[str]:
    """Check that all test directories have __init__.py files."""
    missing_init_files = []

    for root, dirs, files in os.walk(TESTS_ROOT):
        # Skip __pycache__ directories
        if "__pycache__" in root:
            continue

        # Check if the directory has an __init__.py file
        if not os.path.exists(os.path.join(root, "__init__.py")):
            missing_init_files.append(root)

    return missing_init_files


def check_file_patterns() -> Dict[str, List[str]]:
    """Check that test files follow the standard naming patterns."""
    non_compliant_files = {
        "unit": [],
        "integration": [],
        "behavior_feature": [],
        "behavior_steps": [],
    }

    # Check unit tests
    for root, _, files in os.walk(TESTS_ROOT / "unit"):
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, PROJECT_ROOT)
                if not UNIT_TEST_PATTERN.match(rel_path):
                    non_compliant_files["unit"].append(rel_path)

    # Check integration tests
    for root, _, files in os.walk(TESTS_ROOT / "integration"):
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, PROJECT_ROOT)
                if not INTEGRATION_TEST_PATTERN.match(rel_path):
                    non_compliant_files["integration"].append(rel_path)

    # Check behavior feature files
    for root, _, files in os.walk(TESTS_ROOT / "behavior" / "features"):
        for file in files:
            if file.endswith(".feature"):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, PROJECT_ROOT)
                if not BEHAVIOR_FEATURE_PATTERN.match(rel_path):
                    non_compliant_files["behavior_feature"].append(rel_path)

    # Check behavior step files
    for root, _, files in os.walk(TESTS_ROOT / "behavior" / "steps"):
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, PROJECT_ROOT)
                if not BEHAVIOR_STEPS_PATTERN.match(rel_path):
                    non_compliant_files["behavior_steps"].append(rel_path)

    return non_compliant_files


def check_test_classes_with_init() -> List[str]:
    """Check for test classes with __init__ constructors."""
    test_classes_with_init = []

    for root, _, files in os.walk(TESTS_ROOT):
        for file in files:
            if file.endswith(".py") and file.startswith("test_"):
                file_path = os.path.join(root, file)

                # Parse the file with ast
                try:
                    with open(file_path, "r") as f:
                        tree = ast.parse(f.read(), filename=file_path)

                    # Look for classes that might be test classes
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            # Check if it's a test class (name starts with Test)
                            if node.name.startswith("Test"):
                                # Check if it has an __init__ method
                                for item in node.body:
                                    if (
                                        isinstance(item, ast.FunctionDef)
                                        and item.name == "__init__"
                                    ):
                                        rel_path = os.path.relpath(
                                            file_path, PROJECT_ROOT
                                        )
                                        test_classes_with_init.append(
                                            f"{rel_path}::{node.name}"
                                        )
                except Exception as e:
                    print(f"Error parsing {file_path}: {e}")

    return test_classes_with_init


def check_sentinel_files() -> List[str]:
    """Ensure required sentinel test files are present."""
    missing = []
    for path in SENTINEL_TEST_FILES:
        if not path.exists():
            missing.append(os.path.relpath(path, PROJECT_ROOT))
    return missing


def main():
    """Run all checks and report results."""
    print("Verifying test organization standards...")

    # Check for missing __init__.py files
    missing_init_files = check_init_files()
    if missing_init_files:
        print("\n❌ The following directories are missing __init__.py files:")
        for dir_path in missing_init_files:
            print(f"  - {dir_path}")
    else:
        print("\n✅ All test directories have __init__.py files.")

    # Check file patterns
    non_compliant_files = check_file_patterns()
    has_non_compliant_files = any(files for files in non_compliant_files.values())

    if has_non_compliant_files:
        print("\n❌ The following files do not follow the standard naming patterns:")

        if non_compliant_files["unit"]:
            print(
                "\n  Unit tests (should be tests/unit/<module_path>/test_<module_name>.py):"
            )
            for file in non_compliant_files["unit"]:
                print(f"    - {file}")

        if non_compliant_files["integration"]:
            print(
                "\n  Integration tests (should be tests/integration/<feature_area>/test_<feature_name>.py):"
            )
            for file in non_compliant_files["integration"]:
                print(f"    - {file}")

        if non_compliant_files["behavior_feature"]:
            print(
                "\n  Behavior feature files (should be tests/behavior/features/<feature_area>/<feature_name>.feature):"
            )
            for file in non_compliant_files["behavior_feature"]:
                print(f"    - {file}")

        if non_compliant_files["behavior_steps"]:
            print(
                "\n  Behavior step files (should be tests/behavior/steps/test_<feature_name>_steps.py):"
            )
            for file in non_compliant_files["behavior_steps"]:
                print(f"    - {file}")
    else:
        print("\n✅ All test files follow the standard naming patterns.")

    # Check for test classes with __init__ constructors
    test_classes_with_init = check_test_classes_with_init()
    if test_classes_with_init:
        print(
            "\n❌ The following test classes have __init__ constructors (should use pytest fixtures instead):"
        )
        for class_path in test_classes_with_init:
            print(f"  - {class_path}")
    else:
        print("\n✅ No test classes with __init__ constructors found.")

    # Check sentinel test files
    missing_sentinels = check_sentinel_files()
    if missing_sentinels:
        print("\n❌ Missing sentinel test files:")
        for file in missing_sentinels:
            print(f"  - {file}")
    else:
        print("\n✅ All sentinel test files are present.")

    # Overall result
    if (
        missing_init_files
        or has_non_compliant_files
        or test_classes_with_init
        or missing_sentinels
    ):
        print(
            "\n❌ Test organization verification failed. Please fix the issues above."
        )
        return 1
    else:
        print("\n✅ All test organization standards are met!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
