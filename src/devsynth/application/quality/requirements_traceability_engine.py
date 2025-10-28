"""
Requirements Traceability Engine

This module provides automated verification and validation of requirements traceability
throughout the development lifecycle. It ensures that all requirements are properly
linked to specifications, implementation, and tests.

Key features:
- Automated traceability verification of requirements to implementation
- Cross-reference validation between specifications, code, and tests
- BDD feature verification ensuring features are properly referenced
- Traceability gap analysis identifying missing links and coverage
- Traceability reporting with comprehensive traceability matrices
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .dialectical_audit_system import DialecticalAuditSystem, AuditQuestion, DialecticalAuditResult


@dataclass
class TraceabilityLink:
    """Represents a traceability link between artifacts."""

    requirement_id: str
    specification_path: str
    code_path: str
    test_path: str
    link_type: str  # requirement->spec, spec->code, code->test
    valid: bool
    issues: list[str]


@dataclass
class TraceabilityGap:
    """Represents a gap in requirements traceability."""

    requirement_id: str
    gap_type: str  # missing_implementation, missing_tests, missing_docs
    description: str
    priority: str
    effort: str
    impact: str
    suggestions: list[str]


@dataclass
class TraceabilityReport:
    """Comprehensive traceability analysis report."""

    timestamp: str
    project_path: str
    total_requirements: int
    traced_requirements: int
    coverage_percentage: float
    gaps_found: int
    links_validated: int
    invalid_links: int
    gaps: list[TraceabilityGap]
    recommendations: list[str]


class RequirementsTraceabilityEngine:
    """
    Validates requirements traceability matrix.

    This engine ensures that requirements are properly traced through:
    - Requirements to specifications
    - Specifications to implementation
    - Implementation to tests
    - Cross-validation between all artifacts

    It provides gap analysis and recommendations for improving traceability.
    """

    def __init__(self) -> None:
        """Initialize the requirements traceability engine."""
        self.audit_system = DialecticalAuditSystem()

        # Requirement ID patterns
        self.requirement_patterns = [
            r"FR-\d+",  # Functional Requirements
            r"NFR-\d+",  # Non-Functional Requirements
            r"IR-\d+",  # Implementation Requirements
            r"REQ-\d+",  # Generic Requirements
        ]

        # Link patterns in specifications
        self.link_patterns = [
            r"tests/behavior/features/[\w./-]+\.feature",
            r"src/devsynth/[\w./-]+\.py",
            r"docs/specifications/[\w./-]+\.md",
        ]

    def verify_traceability(
        self, matrix_path: Path, spec_dir: Path, code_dir: Path, test_dir: Path
    ) -> tuple[list[str], int, int]:
        """
        Verify requirements traceability.

        Args:
            matrix_path: Path to requirements traceability matrix
            spec_dir: Directory containing specifications
            code_dir: Directory containing source code
            test_dir: Directory containing tests

        Returns:
            Tuple of (errors, requirement_count, specification_count)
        """
        errors = []
        req_count = 0
        spec_count = 0

        if not matrix_path.exists():
            errors.append(f"Requirements traceability matrix not found: {matrix_path}")
            return errors, 0, 0

        try:
            matrix_content = matrix_path.read_text(encoding="utf-8")
            errors.extend(self._verify_matrix_format(matrix_content))
            req_count, spec_count = self._count_requirements_and_specs(matrix_content)

            # Verify each requirement in the matrix
            errors.extend(
                self._verify_matrix_links(matrix_content, spec_dir, code_dir, test_dir)
            )

        except (UnicodeDecodeError, OSError) as e:
            errors.append(f"Could not read traceability matrix: {e}")

        return errors, req_count, spec_count

    def verify_specification_links(self, spec_path: Path) -> list[str]:
        """
        Verify specification contains proper links.

        Args:
            spec_path: Path to the specification file

        Returns:
            List of link errors
        """
        errors = []

        if not spec_path.exists():
            return [f"Specification file not found: {spec_path}"]

        try:
            content = spec_path.read_text(encoding="utf-8")

            # Check for requirement references
            if not self._has_requirement_references(content):
                errors.append(f"{spec_path} missing requirement references")

            # Check for BDD feature references
            if not self._has_bdd_feature_references(content):
                errors.append(f"{spec_path} missing BDD feature references")

            # Check for implementation references
            if not self._has_implementation_references(content):
                errors.append(f"{spec_path} missing implementation references")

            # Validate links are valid
            errors.extend(self._validate_specification_links(content, spec_path))

        except (UnicodeDecodeError, OSError) as e:
            errors.append(f"Could not read specification: {e}")

        return errors

    def verify_bdd_feature_references(self, spec_path: Path) -> list[str]:
        """
        Verify BDD feature files are referenced.

        Args:
            spec_path: Path to the specification file

        Returns:
            List of feature reference errors
        """
        errors = []

        if not spec_path.exists():
            return [f"Specification file not found: {spec_path}"]

        try:
            content = spec_path.read_text(encoding="utf-8")

            # Extract BDD feature references
            feature_refs = self._extract_bdd_references(content)

            if not feature_refs:
                errors.append(f"{spec_path} missing BDD feature references")
            else:
                # Validate that referenced feature files exist
                errors.extend(
                    self._validate_feature_file_references(feature_refs, spec_path)
                )

        except (UnicodeDecodeError, OSError) as e:
            errors.append(f"Could not read specification: {e}")

        return errors

    def verify_code_implementation(
        self, requirement_id: str, code_dir: Path
    ) -> list[str]:
        """
        Verify code implements the specified requirement.

        Args:
            requirement_id: ID of the requirement to verify
            code_dir: Directory containing source code

        Returns:
            List of implementation errors
        """
        errors = []

        if not code_dir.exists():
            return [f"Code directory not found: {code_dir}"]

        # Find code that references this requirement
        code_locations = self._find_requirement_in_code(requirement_id, code_dir)

        if not code_locations:
            errors.append(
                f"No code implementation found for requirement {requirement_id}"
            )

        return errors

    def analyze_traceability_gaps(self, project_root: Path) -> list[TraceabilityGap]:
        """
        Analyze gaps in requirements traceability.

        Args:
            project_root: Root directory of the project

        Returns:
            List of traceability gaps
        """
        gaps = []

        # Run dialectical audit to find inconsistencies
        audit_result = self.audit_system.run_dialectical_audit(str(project_root))

        # Convert audit questions to traceability gaps
        for question in audit_result.questions_generated:
            gap = self._question_to_gap(question)
            if gap:
                gaps.append(gap)

        # Add specific traceability analysis
        gaps.extend(self._analyze_specific_gaps(project_root))

        return gaps

    def generate_traceability_matrix(
        self, project_root: Path, output_format: str = "markdown"
    ) -> str:
        """
        Generate requirements traceability matrix.

        Args:
            project_root: Root directory of the project
            output_format: Output format (markdown, html, json)

        Returns:
            Traceability matrix in specified format
        """
        # Run comprehensive audit
        audit_result = self.audit_system.run_dialectical_audit(str(project_root))

        # Generate matrix based on audit results
        if output_format.lower() == "markdown":
            return self._generate_markdown_matrix(audit_result)
        elif output_format.lower() == "html":
            return self._generate_html_matrix(audit_result)
        elif output_format.lower() == "json":
            return self._generate_json_matrix(audit_result)
        else:
            return self._generate_markdown_matrix(audit_result)  # Default to markdown

    def _verify_matrix_format(self, content: str) -> list[str]:
        """Verify traceability matrix format."""
        errors = []

        lines = content.splitlines()

        # Check for header row
        header_found = False
        for line in lines[:10]:  # Check first 10 lines
            if "| Requirement" in line or "| FR-" in line:
                header_found = True
                break

        if not header_found:
            errors.append("Traceability matrix missing proper header row")

        # Check for required columns
        required_columns = ["requirement", "specification", "code", "test", "status"]
        for column in required_columns:
            if not any(column.lower() in line.lower() for line in lines[:5]):
                errors.append(f"Missing required column: {column}")

        return errors

    def _count_requirements_and_specs(self, content: str) -> tuple[int, int]:
        """Count requirements and specifications in matrix."""
        lines = content.splitlines()
        req_count = 0
        spec_count = 0

        for line in lines:
            # Count requirement rows
            if (
                re.match(r"^\s*\|.*FR-\d+.*\|", line)
                or re.match(r"^\s*\|.*NFR-\d+.*\|", line)
                or re.match(r"^\s*\|.*IR-\d+.*\|", line)
            ):
                req_count += 1

            # Count specification references
            if "docs/specifications/" in line:
                spec_count += 1

        return req_count, spec_count

    def _verify_matrix_links(
        self, content: str, spec_dir: Path, code_dir: Path, test_dir: Path
    ) -> list[str]:
        """Verify links in traceability matrix."""
        errors = []
        lines = content.splitlines()

        for line_num, line in enumerate(lines, 1):
            # Skip header and separator rows
            if not line.strip() or line.startswith("| ---") or "Requirement" in line:
                continue

            # Check if this is a requirement row
            if (
                re.match(r"^\s*\|.*FR-\d+.*\|", line)
                or re.match(r"^\s*\|.*NFR-\d+.*\|", line)
                or re.match(r"^\s*\|.*IR-\d+.*\|", line)
            ):

                parts = [p.strip() for p in line.split("|")[1:-1]]
                if len(parts) < 4:
                    continue

                req_id, spec_cell, code_cell, test_cell = parts[:4]

                # Verify specification link
                if spec_cell and spec_cell.lower() != "n/a":
                    if not self._link_exists(spec_cell, spec_dir):
                        errors.append(
                            f"Line {line_num}: Invalid specification link '{spec_cell}' for {req_id}"
                        )

                # Verify code link
                if code_cell and code_cell.lower() != "n/a":
                    if not self._link_exists(code_cell, code_dir):
                        errors.append(
                            f"Line {line_num}: Invalid code link '{code_cell}' for {req_id}"
                        )

                # Verify test link
                if test_cell and test_cell.lower() != "n/a":
                    if not self._link_exists(test_cell, test_dir):
                        errors.append(
                            f"Line {line_num}: Invalid test link '{test_cell}' for {req_id}"
                        )

        return errors

    def _has_requirement_references(self, content: str) -> bool:
        """Check if content has requirement references."""
        return any(
            re.search(pattern, content, re.IGNORECASE)
            for pattern in self.requirement_patterns
        )

    def _has_bdd_feature_references(self, content: str) -> bool:
        """Check if content has BDD feature references."""
        return bool(re.search(r"tests/behavior/features/[\w./-]+\.feature", content))

    def _has_implementation_references(self, content: str) -> bool:
        """Check if content has implementation references."""
        return bool(re.search(r"src/devsynth/[\w./-]+\.py", content))

    def _validate_specification_links(self, content: str, spec_path: Path) -> list[str]:
        """Validate links in specification."""
        errors = []

        # Find all links in the specification
        links = self._extract_all_links(content)

        for link in links:
            if not self._is_valid_link(link, spec_path.parent):
                errors.append(f"Invalid link: {link}")

        return errors

    def _validate_feature_file_references(
        self, feature_refs: set[str], spec_path: Path
    ) -> list[str]:
        """Validate that referenced feature files exist."""
        errors = []

        repo_root = spec_path.parent.parent.parent  # Go up from docs/specifications/

        for ref in feature_refs:
            # Handle relative paths
            if ref.startswith("./") or ref.startswith("../"):
                feature_path = (spec_path.parent / ref).resolve()
            elif ref.startswith("tests/"):
                feature_path = (repo_root / ref).resolve()
            else:
                feature_path = (
                    repo_root / "tests" / "behavior" / "features" / ref
                ).resolve()

            if not feature_path.exists():
                errors.append(f"Referenced feature file not found: {feature_path}")

        return errors

    def _find_requirement_in_code(
        self, requirement_id: str, code_dir: Path
    ) -> list[str]:
        """Find requirement references in code."""
        locations: list[str] = []

        if not code_dir.exists():
            return locations

        for path in code_dir.rglob("*.py"):
            try:
                content = path.read_text(encoding="utf-8")
                if requirement_id.lower() in content.lower():
                    for line_num, line in enumerate(content.splitlines(), 1):
                        if requirement_id.lower() in line.lower():
                            locations.append(f"{path}:{line_num}")
            except (UnicodeDecodeError, OSError):
                continue

        return locations

    def _question_to_gap(self, question: AuditQuestion) -> TraceabilityGap | None:
        """Convert audit question to traceability gap."""
        if "has tests but is not documented" in question.question:
            return TraceabilityGap(
                requirement_id=question.feature_name,
                gap_type="missing_documentation",
                description=question.question,
                priority="medium",
                effort="low",
                impact="traceability",
                suggestions=[question.suggestion],
            )
        elif "is documented but has no corresponding tests" in question.question:
            return TraceabilityGap(
                requirement_id=question.feature_name,
                gap_type="missing_tests",
                description=question.question,
                priority="high",
                effort="medium",
                impact="verification",
                suggestions=[question.suggestion],
            )
        elif "is implemented in code but not documented or tested" in question.question:
            return TraceabilityGap(
                requirement_id=question.feature_name,
                gap_type="missing_docs_and_tests",
                description=question.question,
                priority="high",
                effort="high",
                impact="completeness",
                suggestions=[question.suggestion],
            )

        return None

    def _analyze_specific_gaps(self, project_root: Path) -> list[TraceabilityGap]:
        """Analyze specific traceability gaps."""
        gaps = []

        # Check for missing test coverage
        gaps.extend(self._analyze_missing_test_coverage(project_root))

        # Check for missing implementation
        gaps.extend(self._analyze_missing_implementation(project_root))

        # Check for missing documentation
        gaps.extend(self._analyze_missing_documentation(project_root))

        return gaps

    def _analyze_missing_test_coverage(
        self, project_root: Path
    ) -> list[TraceabilityGap]:
        """Analyze missing test coverage gaps."""
        gaps = []

        # This would integrate with the enhanced test infrastructure
        # For now, provide placeholder analysis
        test_dir = project_root / "tests"
        if test_dir.exists():
            # Count existing tests
            unit_tests = (
                len(list((test_dir / "unit").rglob("test_*.py")))
                if (test_dir / "unit").exists()
                else 0
            )
            integration_tests = (
                len(list((test_dir / "integration").rglob("test_*.py")))
                if (test_dir / "integration").exists()
                else 0
            )
            behavior_tests = (
                len(list((test_dir / "behavior").rglob("*.feature")))
                if (test_dir / "behavior").exists()
                else 0
            )

            total_tests = unit_tests + integration_tests + behavior_tests

            if total_tests < 10:  # Arbitrary threshold
                gaps.append(
                    TraceabilityGap(
                        requirement_id="GENERAL",
                        gap_type="insufficient_test_coverage",
                        description="Overall test coverage appears insufficient",
                        priority="medium",
                        effort="high",
                        impact="reliability",
                        suggestions=[
                            "Increase unit test coverage",
                            "Add integration tests",
                            "Create BDD scenarios",
                        ],
                    )
                )

        return gaps

    def _analyze_missing_implementation(
        self, project_root: Path
    ) -> list[TraceabilityGap]:
        """Analyze missing implementation gaps."""
        gaps = []

        # Check if there are documented features without implementation
        docs_dir = project_root / "docs" / "specifications"
        if docs_dir.exists():
            for spec_file in docs_dir.rglob("*.md"):
                try:
                    content = spec_file.read_text(encoding="utf-8")

                    # Look for requirement IDs in documentation
                    for pattern in self.requirement_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        for req_id in matches:
                            # Check if requirement is implemented
                            if not self._requirement_is_implemented(
                                req_id, project_root / "src"
                            ):
                                gaps.append(
                                    TraceabilityGap(
                                        requirement_id=req_id,
                                        gap_type="missing_implementation",
                                        description=f"Requirement {req_id} is documented but not implemented",
                                        priority="high",
                                        effort="high",
                                        impact="functionality",
                                        suggestions=[
                                            f"Implement requirement {req_id}",
                                            "Create implementation plan",
                                        ],
                                    )
                                )
                except (UnicodeDecodeError, OSError):
                    continue

        return gaps

    def _analyze_missing_documentation(
        self, project_root: Path
    ) -> list[TraceabilityGap]:
        """Analyze missing documentation gaps."""
        gaps = []

        # Check if there are implemented features without documentation
        src_dir = project_root / "src"
        if src_dir.exists():
            for py_file in src_dir.rglob("*.py"):
                try:
                    content = py_file.read_text(encoding="utf-8")

                    # Look for requirement IDs in code comments
                    for pattern in self.requirement_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        for req_id in matches:
                            # Check if requirement is documented
                            if not self._requirement_is_documented(
                                req_id, project_root / "docs"
                            ):
                                gaps.append(
                                    TraceabilityGap(
                                        requirement_id=req_id,
                                        gap_type="missing_documentation",
                                        description=f"Requirement {req_id} is implemented but not documented",
                                        priority="medium",
                                        effort="medium",
                                        impact="maintainability",
                                        suggestions=[
                                            f"Document requirement {req_id}",
                                            "Create specification",
                                        ],
                                    )
                                )
                except (UnicodeDecodeError, OSError):
                    continue

        return gaps

    def _link_exists(self, link: str, base_dir: Path) -> bool:
        """Check if a link exists in the specified directory."""
        # Handle relative paths
        if link.startswith("./") or link.startswith("../"):
            link_path = base_dir / link
        else:
            link_path = base_dir / link

        return link_path.exists()

    def _extract_bdd_references(self, content: str) -> set[str]:
        """Extract BDD feature references from content."""
        references = set()

        for pattern in self.link_patterns:
            matches = re.findall(pattern, content)
            references.update(matches)

        return references

    def _extract_all_links(self, content: str) -> list[str]:
        """Extract all links from content."""
        links = []

        # Find markdown-style links
        markdown_links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)
        links.extend([link for _, link in markdown_links])

        # Find bare links
        bare_links = re.findall(r"(?:https?://|ftp://|file://)[^\s]+", content)
        links.extend(bare_links)

        # Find relative paths
        relative_paths = re.findall(r'(?:src|tests|docs)/[^\'"\s]+', content)
        links.extend(relative_paths)

        return links

    def _is_valid_link(self, link: str, base_path: Path) -> bool:
        """Check if a link is valid."""
        # Handle different link types
        if link.startswith("http://") or link.startswith("https://"):
            # For HTTP links, we can't easily validate without network access
            return True

        # Handle relative paths
        link_path = base_path / link
        return link_path.exists()

    def _requirement_is_implemented(self, requirement_id: str, code_dir: Path) -> bool:
        """Check if a requirement is implemented in code."""
        return len(self._find_requirement_in_code(requirement_id, code_dir)) > 0

    def _requirement_is_documented(self, requirement_id: str, docs_dir: Path) -> bool:
        """Check if a requirement is documented."""
        return len(self._find_requirement_in_docs(requirement_id, docs_dir)) > 0

    def _find_requirement_in_docs(
        self, requirement_id: str, docs_dir: Path
    ) -> list[str]:
        """Find requirement references in documentation."""
        locations: list[str] = []

        if not docs_dir.exists():
            return locations

        for path in docs_dir.rglob("*.md"):
            try:
                content = path.read_text(encoding="utf-8")
                if requirement_id.lower() in content.lower():
                    for line_num, line in enumerate(content.splitlines(), 1):
                        if requirement_id.lower() in line.lower():
                            locations.append(f"{path}:{line_num}")
            except (UnicodeDecodeError, OSError):
                continue

        return locations

    def _generate_markdown_matrix(self, audit_result: DialecticalAuditResult) -> str:
        """Generate markdown traceability matrix."""
        template = """# Requirements Traceability Matrix

**Generated:** {timestamp}
**Project:** {project_path}
**Coverage:** {coverage_percentage:.1f}%

## Summary

- **Total Features:** {total_features}
- **Inconsistencies:** {inconsistencies}
- **Health Score:** {health_score:.1f}%

## Coverage Analysis

| Artifact | Coverage | Percentage |
|----------|----------|------------|
| Documentation | {docs_covered}/{docs_total} | {docs_percentage:.1f}% |
| Implementation | {code_covered}/{code_total} | {code_percentage:.1f}% |
| Tests | {tests_covered}/{tests_total} | {tests_percentage:.1f}% |

## Feature Matrix

| Feature | Documentation | Implementation | Tests |
|---------|---------------|----------------|-------|
{feature_rows}

## Gaps and Issues

{gaps_section}

## Recommendations

{recommendations}
"""

        # Format feature rows
        feature_rows = []
        for feature, artifacts in audit_result.feature_matrix.items():
            docs_check = "✅" if artifacts.get("docs", False) else "❌"
            code_check = "✅" if artifacts.get("code", False) else "❌"
            tests_check = "✅" if artifacts.get("tests", False) else "❌"
            feature_rows.append(
                f"| {feature} | {docs_check} | {code_check} | {tests_check} |"
            )

        # Format gaps section
        gaps_section = ""
        if audit_result.questions_generated:
            gaps_section = "\n".join(
                f"- {q.question}" for q in audit_result.questions_generated[:10]
            )
            if len(audit_result.questions_generated) > 10:
                gaps_section += f"\n- ... and {len(audit_result.questions_generated) - 10} more issues"

        # Format recommendations
        recommendations = "\n".join(
            f"- {rec}" for rec in audit_result.audit_summary.get("recommendations", [])
        )

        return template.format(
            timestamp=audit_result.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            project_path=audit_result.project_path,
            coverage_percentage=audit_result.audit_summary.get("health_score", 0),
            total_features=audit_result.total_features_found,
            inconsistencies=audit_result.inconsistencies_found,
            health_score=audit_result.audit_summary.get("health_score", 0),
            docs_covered=audit_result.coverage_analysis.get("docs", {}).get(
                "covered", 0
            ),
            docs_total=audit_result.coverage_analysis.get("docs", {}).get("total", 0),
            docs_percentage=audit_result.coverage_analysis.get("docs", {}).get(
                "percentage", 0
            ),
            code_covered=audit_result.coverage_analysis.get("code", {}).get(
                "covered", 0
            ),
            code_total=audit_result.coverage_analysis.get("code", {}).get("total", 0),
            code_percentage=audit_result.coverage_analysis.get("code", {}).get(
                "percentage", 0
            ),
            tests_covered=audit_result.coverage_analysis.get("tests", {}).get(
                "covered", 0
            ),
            tests_total=audit_result.coverage_analysis.get("tests", {}).get("total", 0),
            tests_percentage=audit_result.coverage_analysis.get("tests", {}).get(
                "percentage", 0
            ),
            feature_rows="\n".join(feature_rows),
            gaps_section=gaps_section,
            recommendations=recommendations,
        )

    def _generate_html_matrix(self, audit_result: DialecticalAuditResult) -> str:
        """Generate HTML traceability matrix."""
        template = """<!DOCTYPE html>
<html>
<head>
    <title>Requirements Traceability Matrix</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #f8f9fa; padding: 20px; border-radius: 5px; }}
        .summary {{ background: #e9ecef; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .status-yes {{ color: green; font-weight: bold; }}
        .status-no {{ color: red; font-weight: bold; }}
        .gap {{ background: #fff3cd; padding: 10px; margin: 5px 0; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Requirements Traceability Matrix</h1>
        <p><strong>Generated:</strong> {timestamp}</p>
        <p><strong>Project:</strong> {project_path}</p>
    </div>

    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Total Features:</strong> {total_features}</p>
        <p><strong>Inconsistencies:</strong> {inconsistencies}</p>
        <p><strong>Health Score:</strong> {health_score:.1f}%</p>
    </div>

    <h2>Coverage Analysis</h2>
    <table>
        <tr><th>Artifact</th><th>Covered</th><th>Total</th><th>Percentage</th></tr>
        <tr><td>Documentation</td><td>{docs_covered}</td><td>{docs_total}</td><td>{docs_percentage:.1f}%</td></tr>
        <tr><td>Implementation</td><td>{code_covered}</td><td>{code_total}</td><td>{code_percentage:.1f}%</td></tr>
        <tr><td>Tests</td><td>{tests_covered}</td><td>{tests_total}</td><td>{tests_percentage:.1f}%</td></tr>
    </table>

    <h2>Feature Matrix</h2>
    <table>
        <tr><th>Feature</th><th>Documentation</th><th>Implementation</th><th>Tests</th></tr>
        {feature_rows}
    </table>

    <h2>Gaps and Issues</h2>
    {gaps_section}

    <h2>Recommendations</h2>
    {recommendations}
</body>
</html>"""

        # Format feature rows
        feature_rows = []
        for feature, artifacts in audit_result.feature_matrix.items():
            docs_status = (
                '<span class="status-yes">✓</span>'
                if artifacts.get("docs", False)
                else '<span class="status-no">✗</span>'
            )
            code_status = (
                '<span class="status-yes">✓</span>'
                if artifacts.get("code", False)
                else '<span class="status-no">✗</span>'
            )
            tests_status = (
                '<span class="status-yes">✓</span>'
                if artifacts.get("tests", False)
                else '<span class="status-no">✗</span>'
            )
            feature_rows.append(
                f"<tr><td>{feature}</td><td>{docs_status}</td><td>{code_status}</td><td>{tests_status}</td></tr>"
            )

        # Format gaps section
        gaps_section = ""
        if audit_result.questions_generated:
            gaps_section = "\n".join(
                f'<div class="gap">{q.question}</div>'
                for q in audit_result.questions_generated[:10]
            )

        # Format recommendations
        recommendations = "\n".join(
            f'<div class="recommendation">{rec}</div>'
            for rec in audit_result.audit_summary.get("recommendations", [])
        )

        return template.format(
            timestamp=audit_result.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            project_path=audit_result.project_path,
            total_features=audit_result.total_features_found,
            inconsistencies=audit_result.inconsistencies_found,
            health_score=audit_result.audit_summary.get("health_score", 0),
            docs_covered=audit_result.coverage_analysis.get("docs", {}).get(
                "covered", 0
            ),
            docs_total=audit_result.coverage_analysis.get("docs", {}).get("total", 0),
            docs_percentage=audit_result.coverage_analysis.get("docs", {}).get(
                "percentage", 0
            ),
            code_covered=audit_result.coverage_analysis.get("code", {}).get(
                "covered", 0
            ),
            code_total=audit_result.coverage_analysis.get("code", {}).get("total", 0),
            code_percentage=audit_result.coverage_analysis.get("code", {}).get(
                "percentage", 0
            ),
            tests_covered=audit_result.coverage_analysis.get("tests", {}).get(
                "covered", 0
            ),
            tests_total=audit_result.coverage_analysis.get("tests", {}).get("total", 0),
            tests_percentage=audit_result.coverage_analysis.get("tests", {}).get(
                "percentage", 0
            ),
            feature_rows="\n".join(feature_rows),
            gaps_section=gaps_section,
            recommendations=recommendations,
        )

    def _generate_json_matrix(self, audit_result: DialecticalAuditResult) -> str:
        """Generate JSON traceability matrix."""
        import json

        data = {
            "timestamp": audit_result.timestamp.isoformat(),
            "project_path": audit_result.project_path,
            "total_features": audit_result.total_features_found,
            "inconsistencies": audit_result.inconsistencies_found,
            "health_score": audit_result.audit_summary.get("health_score", 0),
            "coverage_analysis": audit_result.coverage_analysis,
            "feature_matrix": audit_result.feature_matrix,
            "questions": [q.question for q in audit_result.questions_generated],
            "recommendations": audit_result.audit_summary.get("recommendations", []),
        }

        return json.dumps(data, indent=2, default=str)
