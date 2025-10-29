#!/usr/bin/env python3
"""Update requirements traceability matrix based on source code and tests.

Scans the codebase to identify requirements, specifications, behavior tests,
and unit tests, then updates the traceability matrix accordingly.
"""
from __future__ import annotations

import pathlib
import re
import sys
from typing import Dict, List, Set, Tuple

import yaml


def extract_requirements_from_spec(spec_file: pathlib.Path) -> List[Tuple[str, str]]:
    """Extract FR and NFR requirements from system requirements specification."""
    requirements = []
    content = spec_file.read_text()

    # Match FR-XX and NFR-XX patterns
    fr_pattern = r'- \[([A-Z]+-\d+(?:[a-z])?)\] (.+?)(?=\n- \[|$)'
    matches = re.findall(fr_pattern, content, re.DOTALL)

    for req_id, description in matches:
        # Clean up the description
        description = description.strip()
        # Remove any trailing content after the main description
        description = re.split(r'\n\s*- \[|$', description, 1)[0].strip()
        requirements.append((req_id, description))

    return requirements


def find_specification_files(specs_dir: pathlib.Path) -> Dict[str, pathlib.Path]:
    """Find all published specification files."""
    specs = {}
    for spec_file in specs_dir.glob("*.md"):
        if spec_file.name in {"index.md", "spec_template.md"}:
            continue

        content = spec_file.read_text()
        # Check if status is published
        if re.search(r'^status:\s*published', content, re.MULTILINE):
            # Extract title
            title_match = re.search(r'^title:\s*(.+)$', content, re.MULTILINE)
            if title_match:
                title = title_match.group(1).strip()
                specs[title] = spec_file

    return specs


def find_behavior_tests(behavior_dir: pathlib.Path) -> Dict[str, pathlib.Path]:
    """Find all behavior test feature files."""
    features = {}
    for feature_file in behavior_dir.glob("**/*.feature"):
        content = feature_file.read_text()
        # Extract feature name from the first Feature line
        feature_match = re.search(r'^Feature:\s*(.+)$', content, re.MULTILINE)
        if feature_match:
            feature_name = feature_match.group(1).strip()
            features[feature_name] = feature_file
    return features


def find_unit_tests(unit_dir: pathlib.Path) -> Dict[str, List[pathlib.Path]]:
    """Find unit test files grouped by component."""
    unit_tests = {}
    for test_file in unit_dir.glob("**/*.py"):
        if test_file.name.startswith("test_"):
            # Extract component name from path
            parts = test_file.relative_to(unit_dir).parts
            if len(parts) > 1:
                component = parts[0]
            else:
                component = "general"

            if component not in unit_tests:
                unit_tests[component] = []
            unit_tests[component].append(test_file)
    return unit_tests


def find_code_modules(src_dir: pathlib.Path) -> Dict[str, List[pathlib.Path]]:
    """Find code modules by component."""
    modules = {}
    for py_file in src_dir.glob("**/*.py"):
        # Skip __init__.py and test files
        if py_file.name == "__init__.py" or py_file.name.startswith("test_"):
            continue

        # Extract component name from path
        parts = py_file.relative_to(src_dir).parts
        if len(parts) > 1:
            component = parts[0]
        else:
            component = "core"

        if component not in modules:
            modules[component] = []
        modules[component].append(py_file)
    return modules


def generate_traceability_matrix(
    requirements: List[Tuple[str, str]],
    specs: Dict[str, pathlib.Path],
    behavior_tests: Dict[str, pathlib.Path],
    unit_tests: Dict[str, List[pathlib.Path]],
    code_modules: Dict[str, List[pathlib.Path]],
    project_root: pathlib.Path
) -> str:
    """Generate markdown traceability matrix."""

    # Group requirements by type/prefix
    fr_requirements = [(rid, desc) for rid, desc in requirements if rid.startswith('FR-')]
    nfr_requirements = [(rid, desc) for rid, desc in requirements if rid.startswith('NFR-')]
    other_requirements = [(rid, desc) for rid, desc in requirements if not (rid.startswith('FR-') or rid.startswith('NFR-'))]

    matrix_lines = [
        "## Requirements Traceability Matrix",
        "",
        "## Summary",
        "",
        f"- Functional requirements: {len(fr_requirements)} total",
        f"- Non-functional requirements: {len(nfr_requirements)} total",
        f"- Other requirements: {len(other_requirements)} total",
        f"- Published specifications: {len(specs)} total",
        f"- Behavior test features: {len(behavior_tests)} total",
        "",
        "## Functional Requirements",
        "",
        "| Requirement | Specification sources | Behaviour coverage | Unit coverage |",
        "| --- | --- | --- | --- |"
    ]

    # Add functional requirements
    for req_id, description in fr_requirements:
        spec_refs = find_related_specs(req_id, description, specs, project_root)
        behavior_refs = find_related_behavior_tests(req_id, description, behavior_tests, project_root)
        unit_refs = find_related_unit_tests(req_id, description, unit_tests, project_root)

        matrix_lines.append(
            f"| {req_id} — {description} | {spec_refs} | {behavior_refs} | {unit_refs} |"
        )

    # Add non-functional requirements if any
    if nfr_requirements:
        matrix_lines.extend([
            "",
            "## Non-Functional Requirements",
            "",
            "| Requirement | Specification sources | Behaviour coverage | Unit coverage |",
            "| --- | --- | --- | --- |"
        ])

        for req_id, description in nfr_requirements:
            spec_refs = find_related_specs(req_id, description, specs, project_root)
            behavior_refs = find_related_behavior_tests(req_id, description, behavior_tests, project_root)
            unit_refs = find_related_unit_tests(req_id, description, unit_tests, project_root)

            matrix_lines.append(
                f"| {req_id} — {description} | {spec_refs} | {behavior_refs} | {unit_refs} |"
            )

    # Add other requirements if any
    if other_requirements:
        matrix_lines.extend([
            "",
            "## Other Requirements",
            "",
            "| Requirement | Specification sources | Behaviour coverage | Unit coverage |",
            "| --- | --- | --- | --- |"
        ])

        for req_id, description in other_requirements:
            spec_refs = find_related_specs(req_id, description, specs, project_root)
            behavior_refs = find_related_behavior_tests(req_id, description, behavior_tests, project_root)
            unit_refs = find_related_unit_tests(req_id, description, unit_tests, project_root)

            matrix_lines.append(
                f"| {req_id} — {description} | {spec_refs} | {behavior_refs} | {unit_refs} |"
            )

    return "\n".join(matrix_lines)


def find_related_specs(req_id: str, description: str, specs: Dict[str, pathlib.Path], project_root: pathlib.Path) -> str:
    """Find specifications related to a requirement."""
    related = []

    # Simple keyword matching - could be enhanced with more sophisticated matching
    keywords = set(description.lower().split())
    keywords.update(req_id.lower().split('-'))

    for spec_title, spec_file in specs.items():
        spec_content = spec_file.read_text().lower()
        if any(keyword in spec_content for keyword in keywords):
            relative_path = spec_file.relative_to(project_root)
            related.append(f"【F:{relative_path}†L1-L100】")  # Placeholder line refs

    return "; ".join(related) if related else "TBD"


def find_related_behavior_tests(req_id: str, description: str, behavior_tests: Dict[str, pathlib.Path], project_root: pathlib.Path) -> str:
    """Find behavior tests related to a requirement."""
    related = []

    keywords = set(description.lower().split())
    keywords.update(req_id.lower().split('-'))

    for feature_name, feature_file in behavior_tests.items():
        feature_content = feature_file.read_text().lower()
        if any(keyword in feature_content for keyword in keywords):
            relative_path = feature_file.relative_to(project_root)
            related.append(f"【F:{relative_path}†L1-L50】")  # Placeholder line refs

    return "; ".join(related) if related else "TBD"


def find_related_unit_tests(req_id: str, description: str, unit_tests: Dict[str, List[pathlib.Path]], project_root: pathlib.Path) -> str:
    """Find unit tests related to a requirement."""
    related = []

    keywords = set(description.lower().split())
    keywords.update(req_id.lower().split('-'))

    for component, test_files in unit_tests.items():
        for test_file in test_files:
            test_content = test_file.read_text().lower()
            if any(keyword in test_content for keyword in keywords):
                relative_path = test_file.relative_to(project_root)
                related.append(f"【F:{relative_path}†L1-L100】")  # Placeholder line refs

    return "; ".join(related) if related else "TBD"


def main() -> int:
    """Main entry point for traceability update."""
    project_root = pathlib.Path(__file__).parent.parent

    # Paths
    specs_dir = project_root / "docs" / "specifications"
    behavior_dir = project_root / "tests" / "behavior" / "features"
    unit_dir = project_root / "tests" / "unit"
    src_dir = project_root / "src" / "devsynth"
    sys_req_file = project_root / "docs" / "system_requirements_specification.md"
    traceability_file = project_root / "docs" / "requirements_traceability.md"

    try:
        # Extract data
        requirements = extract_requirements_from_spec(sys_req_file)
        specs = find_specification_files(specs_dir)
        behavior_tests = find_behavior_tests(behavior_dir)
        unit_tests = find_unit_tests(unit_dir)
        code_modules = find_code_modules(src_dir)

        # Generate new matrix
        matrix_content = generate_traceability_matrix(
            requirements, specs, behavior_tests, unit_tests, code_modules, project_root
        )

        # Read existing traceability file
        existing_content = traceability_file.read_text()

        # Find the matrix section and replace it
        # Look for "## Requirements Traceability Matrix" and replace everything after it
        matrix_start = existing_content.find("## Requirements Traceability Matrix")
        if matrix_start != -1:
            # Keep the header/front matter
            header_content = existing_content[:matrix_start]
            new_content = header_content + matrix_content
        else:
            # Fallback: replace entire file
            new_content = matrix_content

        # Write updated file
        traceability_file.write_text(new_content)

        print(f"[update_traceability] Updated {traceability_file}")
        print(f"[update_traceability] Found {len(requirements)} requirements, {len(specs)} specs, {len(behavior_tests)} behavior tests")
        return 0

    except Exception as e:
        print(f"[update_traceability] Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
