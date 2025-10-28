#!/usr/bin/env python3
"""
Metadata Validation Script for DevSynth Documentation Harmonization

This script validates and standardizes metadata across all documentation files,
ensuring consistent YAML frontmatter structure and content.
"""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import yaml

STANDARD_METADATA_SCHEMA = {
    "required": ["title", "date", "version", "status", "author"],
    "optional": ["tags", "last_reviewed", "generated", "generator"],
    "valid_statuses": ["published", "draft", "archived", "active"],
    "standard_version": "0.1.0-alpha.1",
    "standard_author": "DevSynth Team",
}


def extract_frontmatter(file_path: Path) -> tuple[dict | None, str, list[str]]:
    """Extract YAML frontmatter from a markdown file. Returns (metadata, content, lines)."""
    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        return None, "", []

    content = "".join(lines)

    # Check for YAML frontmatter
    if content.startswith("---\n"):
        try:
            # Find the end of frontmatter
            end_match = re.search(r"\n---\n", content[4:])
            if end_match:
                frontmatter_text = content[4 : end_match.start() + 4]
                remaining_content = content[end_match.end() + 4 :]

                # Parse YAML
                frontmatter = yaml.safe_load(frontmatter_text)
                return frontmatter, remaining_content, lines
        except yaml.YAMLError as e:
            print(f"YAML parsing error in {file_path}: {e}")

    return None, content, lines


def validate_metadata(file_path: Path, metadata: dict | None) -> list[dict]:
    """Validate metadata against standard schema. Returns list of issues."""
    issues = []

    if metadata is None:
        issues.append(
            {
                "type": "missing_frontmatter",
                "severity": "error",
                "message": "File has no YAML frontmatter",
                "suggestion": "Add standard metadata header",
            }
        )
        return issues

    # Check required fields
    for field in STANDARD_METADATA_SCHEMA["required"]:
        if field not in metadata:
            issues.append(
                {
                    "type": "missing_required_field",
                    "severity": "error",
                    "field": field,
                    "message": f'Required field "{field}" is missing',
                    "suggestion": f"Add {field} to frontmatter",
                }
            )

    # Validate status
    if "status" in metadata:
        if metadata["status"] not in STANDARD_METADATA_SCHEMA["valid_statuses"]:
            issues.append(
                {
                    "type": "invalid_status",
                    "severity": "warning",
                    "field": "status",
                    "value": metadata["status"],
                    "message": f'Status "{metadata["status"]}" is not in valid list',
                    "suggestion": f'Use one of: {", ".join(STANDARD_METADATA_SCHEMA["valid_statuses"])}',
                }
            )

    # Validate version consistency
    if "version" in metadata:
        if metadata["version"] != STANDARD_METADATA_SCHEMA["standard_version"]:
            issues.append(
                {
                    "type": "version_inconsistency",
                    "severity": "info",
                    "field": "version",
                    "value": metadata["version"],
                    "message": f"Version differs from standard",
                    "suggestion": f'Consider updating to {STANDARD_METADATA_SCHEMA["standard_version"]}',
                }
            )

    # Validate date format
    if "date" in metadata:
        date_str = str(metadata["date"])
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            issues.append(
                {
                    "type": "invalid_date_format",
                    "severity": "warning",
                    "field": "date",
                    "value": date_str,
                    "message": "Date format should be YYYY-MM-DD",
                    "suggestion": "Use ISO date format (YYYY-MM-DD)",
                }
            )

    return issues


def generate_standard_metadata(
    file_path: Path, existing_metadata: dict | None = None
) -> dict:
    """Generate standard metadata for a file."""
    # Extract title from filename if not provided
    title = file_path.stem.replace("_", " ").replace("-", " ").title()
    if title.lower() == "index":
        parent_dir = file_path.parent.name.replace("_", " ").title()
        title = parent_dir

    # Base metadata
    metadata = {
        "title": title,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "version": STANDARD_METADATA_SCHEMA["standard_version"],
        "status": "published",
        "author": STANDARD_METADATA_SCHEMA["standard_author"],
        "last_reviewed": datetime.now().strftime("%Y-%m-%d"),
    }

    # Preserve existing metadata where appropriate
    if existing_metadata:
        # Preserve title if it exists and is meaningful
        if "title" in existing_metadata and existing_metadata["title"].strip():
            metadata["title"] = existing_metadata["title"]

        # Preserve tags
        if "tags" in existing_metadata:
            metadata["tags"] = existing_metadata["tags"]

        # Preserve status if valid
        if (
            "status" in existing_metadata
            and existing_metadata["status"]
            in STANDARD_METADATA_SCHEMA["valid_statuses"]
        ):
            metadata["status"] = existing_metadata["status"]

        # Preserve original date if it exists
        if "date" in existing_metadata:
            metadata["date"] = existing_metadata["date"]

        # Preserve generated flag
        if "generated" in existing_metadata:
            metadata["generated"] = existing_metadata["generated"]
            metadata["generator"] = existing_metadata.get("generator", "unknown")

    return metadata


def format_metadata_yaml(metadata: dict) -> str:
    """Format metadata as YAML frontmatter."""
    yaml_content = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
    return f"---\n{yaml_content}---\n"


def validate_all_documentation(docs_dir: Path) -> dict:
    """Validate metadata across all documentation files."""
    results = {
        "files_processed": 0,
        "files_with_issues": 0,
        "total_issues": 0,
        "issues_by_type": {},
        "files_without_metadata": [],
        "files_with_errors": [],
        "validation_details": [],
    }

    # Find all markdown files
    for md_file in docs_dir.rglob("*.md"):
        # Skip archived content and certain generated files
        if any(skip in str(md_file) for skip in ["archived/", "tmp_", ".git/"]):
            continue

        results["files_processed"] += 1

        metadata, content, lines = extract_frontmatter(md_file)
        issues = validate_metadata(md_file, metadata)

        if issues:
            results["files_with_issues"] += 1
            results["total_issues"] += len(issues)

            for issue in issues:
                issue_type = issue["type"]
                if issue_type not in results["issues_by_type"]:
                    results["issues_by_type"][issue_type] = 0
                results["issues_by_type"][issue_type] += 1

        if metadata is None:
            results["files_without_metadata"].append(
                str(md_file.relative_to(docs_dir.parent))
            )

        results["validation_details"].append(
            {
                "file": str(md_file.relative_to(docs_dir.parent)),
                "has_metadata": metadata is not None,
                "issues": issues,
            }
        )

    return results


def generate_validation_report(results: dict) -> str:
    """Generate a comprehensive validation report."""
    files_processed = results["files_processed"]
    files_with_issues = results["files_with_issues"]
    total_issues = results["total_issues"]

    compliance_rate = (
        ((files_processed - files_with_issues) / files_processed * 100)
        if files_processed > 0
        else 0
    )

    report = f"""
METADATA VALIDATION REPORT
{'=' * 50}

Summary:
- Files processed: {files_processed}
- Files with issues: {files_with_issues}
- Files compliant: {files_processed - files_with_issues}
- Total issues found: {total_issues}
- Compliance rate: {compliance_rate:.1f}%

"""

    if results["issues_by_type"]:
        report += "Issues by Type:\n"
        for issue_type, count in sorted(results["issues_by_type"].items()):
            report += f"- {issue_type}: {count}\n"
        report += "\n"

    if results["files_without_metadata"]:
        report += (
            f"Files Without Metadata ({len(results['files_without_metadata'])}):\n"
        )
        for file_path in results["files_without_metadata"][:10]:  # Show first 10
            report += f"- {file_path}\n"
        if len(results["files_without_metadata"]) > 10:
            report += (
                f"... and {len(results['files_without_metadata']) - 10} more files\n"
            )
        report += "\n"

    # Show detailed issues for files with problems
    files_with_detailed_issues = [
        f for f in results["validation_details"] if f["issues"]
    ]
    if files_with_detailed_issues:
        report += f"Detailed Issues ({len(files_with_detailed_issues)} files):\n"
        report += "-" * 40 + "\n"

        for file_info in files_with_detailed_issues[:20]:  # Show first 20
            report += f"\n📁 {file_info['file']}\n"
            for issue in file_info["issues"]:
                severity_icon = (
                    "❌"
                    if issue["severity"] == "error"
                    else "⚠️" if issue["severity"] == "warning" else "ℹ️"
                )
                report += f"   {severity_icon} {issue['message']}\n"
                if "suggestion" in issue:
                    report += f"      → {issue['suggestion']}\n"

        if len(files_with_detailed_issues) > 20:
            report += f"\n... and {len(files_with_detailed_issues) - 20} more files with issues\n"

    report += "\n" + "=" * 50 + "\n"
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Validate metadata in documentation files"
    )
    parser.add_argument(
        "--docs-dir", default="docs", help="Documentation directory to validate"
    )
    parser.add_argument(
        "--report", action="store_true", help="Generate detailed report"
    )
    parser.add_argument("--strict", action="store_true", help="Strict validation mode")
    parser.add_argument("--report-file", help="Save report to file")

    args = parser.parse_args()

    docs_dir = Path(args.docs_dir)
    if not docs_dir.exists():
        print(f"Error: Documentation directory '{docs_dir}' not found")
        sys.exit(1)

    print(f"Validating metadata in: {docs_dir}")
    results = validate_all_documentation(docs_dir)

    if args.report or args.strict:
        report = generate_validation_report(results)
        print(report)

        if args.report_file:
            try:
                with open(args.report_file, "w", encoding="utf-8") as f:
                    f.write(report)
                print(f"Report saved to: {args.report_file}")
            except Exception as e:
                print(f"Error saving report: {e}")
    else:
        print(f"Files processed: {results['files_processed']}")
        print(f"Files with issues: {results['files_with_issues']}")
        print(
            f"Compliance rate: {((results['files_processed'] - results['files_with_issues']) / results['files_processed'] * 100):.1f}%"
        )

    # Exit with error code in strict mode if there are issues
    if args.strict and results["files_with_issues"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
