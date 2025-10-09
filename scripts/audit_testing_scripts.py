#!/usr/bin/env python3
"""
Testing Script Audit Tool

This script scans the scripts/ directory for all testing-related scripts and:
- Categorizes scripts by functionality (test execution, coverage, validation, etc.)
- Identifies overlapping functionality between scripts
- Generates consolidation recommendations
- Creates migration mapping from old scripts to new CLI commands
- Outputs structured reports in JSON and Markdown formats
- Includes usage frequency analysis based on git history

Usage:
    python scripts/audit_testing_scripts.py [--output-json FILE] [--output-md FILE] [--include-git-history]

Examples:
    # Basic audit
    python scripts/audit_testing_scripts.py

    # With git history analysis
    python scripts/audit_testing_scripts.py --include-git-history

    # Custom output files
    python scripts/audit_testing_scripts.py --output-json audit.json --output-md audit.md
"""

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class ScriptAnalyzer:
    """Analyzes individual scripts for functionality and dependencies."""

    def __init__(self) -> None:
        # Categories for script classification
        self.categories = {
            "test_execution": {
                "keywords": [
                    "run_tests",
                    "execute_test",
                    "pytest",
                    "test_runner",
                    "run_all_tests",
                ],
                "description": "Scripts that execute test suites",
            },
            "coverage": {
                "keywords": ["coverage", "cov", "htmlcov", "coverage_report"],
                "description": "Scripts related to code coverage analysis",
            },
            "validation": {
                "keywords": ["verify", "validate", "check", "audit", "lint"],
                "description": "Scripts that validate code, configuration, or compliance",
            },
            "test_categorization": {
                "keywords": ["categorize", "marker", "speed", "test_markers"],
                "description": "Scripts that categorize or mark tests",
            },
            "test_infrastructure": {
                "keywords": ["infrastructure", "fixture", "conftest", "test_utils"],
                "description": "Scripts that manage test infrastructure",
            },
            "performance": {
                "keywords": ["benchmark", "performance", "speed", "timing"],
                "description": "Scripts for performance testing and analysis",
            },
            "reporting": {
                "keywords": ["report", "metrics", "summary", "dashboard"],
                "description": "Scripts that generate reports or metrics",
            },
            "maintenance": {
                "keywords": ["clean", "fix", "repair", "update"],
                "description": "Scripts for maintenance and cleanup",
            },
        }

    def analyze_script(self, script_path: Path) -> Dict[str, Any]:
        """Analyze a single script file."""
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Basic file info
            result = {
                "path": str(script_path),
                "name": script_path.name,
                "size": len(content),
                "lines": len(content.split("\n")),
                "executable": os.access(script_path, os.X_OK),
                "categories": [],
                "functions": [],
                "imports": [],
                "dependencies": [],
                "description": "",
                "usage_patterns": [],
            }

            # Extract docstring description
            if content.strip():
                try:
                    tree = ast.parse(content)
                    if (
                        tree.body
                        and isinstance(tree.body[0], ast.Expr)
                        and isinstance(tree.body[0].value, ast.Constant)
                        and isinstance(tree.body[0].value.value, str)
                    ):
                        result["description"] = tree.body[0].value.value.strip()[:200]
                except:
                    pass

            # If no docstring, extract from comments
            if not result["description"]:
                for line in content.split("\n")[:10]:
                    if line.strip().startswith("#") and len(line.strip()) > 2:
                        result["description"] = line.strip()[1:].strip()[:200]
                        break

            # Categorize script
            script_name_lower = script_path.name.lower()
            content_lower = content.lower()

            for category, info in self.categories.items():
                if any(
                    keyword in script_name_lower or keyword in content_lower
                    for keyword in info["keywords"]
                ):
                    result["categories"].append(category)

            # Extract functions (if Python)
            if script_path.suffix == ".py":
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            result["functions"].append(node.name)
                        elif isinstance(node, ast.Import):
                            for alias in node.names:
                                result["imports"].append(alias.name)
                        elif isinstance(node, ast.ImportFrom) and node.module:
                            result["imports"].append(node.module)
                except:
                    pass

            # Find pytest/testing dependencies
            testing_patterns = [
                r"pytest",
                r"coverage",
                r"unittest",
                r"test_",
                r"@pytest",
                r"--cov",
                r"-m\s+\w+",
                r"pytest.main",
                r"subprocess.*pytest",
            ]

            for pattern in testing_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    result["dependencies"].append(pattern)

            # Extract usage patterns from argparse or similar
            if "argparse" in content or "ArgumentParser" in content:
                # Try to extract command line patterns
                arg_patterns = re.findall(
                    r'add_argument\([\'"]([^\'\"]+)[\'"]', content
                )
                result["usage_patterns"].extend(arg_patterns)

            return result

        except Exception as e:
            return {
                "path": str(script_path),
                "name": script_path.name,
                "error": str(e),
                "analyzable": False,
            }


class ScriptAuditor:
    """Main class for auditing testing scripts."""

    def __init__(self, scripts_dir: Path) -> None:
        self.scripts_dir = scripts_dir
        self.analyzer = ScriptAnalyzer()
        self.scripts: List[Dict[str, Any]] = []

    def find_testing_scripts(self) -> List[Path]:
        """Find all testing-related scripts."""
        testing_patterns = [
            "test*",
            "*test*",
            "*coverage*",
            "*pytest*",
            "verify*",
            "validate*",
            "check*",
            "run_*",
            "*_test",
            "audit*",
        ]

        found_scripts = set()

        # Find by filename patterns
        for pattern in testing_patterns:
            for script_path in self.scripts_dir.rglob(pattern):
                if script_path.is_file() and script_path.suffix in [".py", ".sh"]:
                    found_scripts.add(script_path)

        # Also scan all scripts for testing-related content
        for script_path in self.scripts_dir.rglob("*.py"):
            if script_path.is_file():
                try:
                    with open(script_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    if any(
                        keyword in content.lower()
                        for keyword in [
                            "pytest",
                            "test_",
                            "coverage",
                            "unittest",
                            "@pytest.mark",
                        ]
                    ):
                        found_scripts.add(script_path)
                except:
                    pass

        return sorted(found_scripts)

    def get_git_usage_frequency(self, script_path: Path) -> Dict[str, Any]:
        """Get git usage statistics for a script."""
        try:
            # Get commit count
            result = subprocess.run(
                ["git", "log", "--oneline", "--", str(script_path)],
                capture_output=True,
                text=True,
                cwd=self.scripts_dir.parent,
            )

            commit_count = (
                len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0
            )

            # Get last modification date
            result = subprocess.run(
                [
                    "git",
                    "log",
                    "-1",
                    "--format=%cd",
                    "--date=iso",
                    "--",
                    str(script_path),
                ],
                capture_output=True,
                text=True,
                cwd=self.scripts_dir.parent,
            )

            last_modified = (
                result.stdout.strip() if result.returncode == 0 else "unknown"
            )

            # Get creation date
            result = subprocess.run(
                [
                    "git",
                    "log",
                    "--reverse",
                    "--format=%cd",
                    "--date=iso",
                    "--",
                    str(script_path),
                ],
                capture_output=True,
                text=True,
                cwd=self.scripts_dir.parent,
            )

            first_line = (
                result.stdout.strip().split("\n")[0] if result.stdout.strip() else ""
            )
            created_date = first_line if first_line else "unknown"

            return {
                "commit_count": commit_count,
                "last_modified": last_modified,
                "created_date": created_date,
                "frequency_score": commit_count,  # Simple scoring
            }

        except Exception as e:
            return {
                "commit_count": 0,
                "last_modified": "unknown",
                "created_date": "unknown",
                "frequency_score": 0,
                "error": str(e),
            }

    def analyze_overlaps(self) -> Dict[str, Any]:
        """Analyze overlapping functionality between scripts."""
        overlaps = defaultdict(list)
        category_groups = defaultdict(list)

        # Group by categories
        for script in self.scripts:
            for category in script.get("categories", []):
                category_groups[category].append(script)

        # Find overlaps within categories
        for category, scripts_in_category in category_groups.items():
            if len(scripts_in_category) > 1:
                overlaps[category] = [
                    {
                        "name": s["name"],
                        "path": s["path"],
                        "functions": s.get("functions", []),
                        "description": s.get("description", "")[:100],
                    }
                    for s in scripts_in_category
                ]

        # Find functional overlaps (similar function names)
        function_overlaps = defaultdict(list)
        for script in self.scripts:
            for func in script.get("functions", []):
                function_overlaps[func].append(script["name"])

        # Keep only functions that appear in multiple scripts
        duplicate_functions = {
            func: scripts
            for func, scripts in function_overlaps.items()
            if len(scripts) > 1
        }

        return {
            "category_overlaps": dict(overlaps),
            "duplicate_functions": duplicate_functions,
            "overlap_summary": {
                "categories_with_overlaps": len(overlaps),
                "duplicate_function_count": len(duplicate_functions),
            },
        }

    def generate_consolidation_recommendations(self) -> Dict[str, Any]:
        """Generate recommendations for script consolidation."""
        recommendations = {
            "immediate_candidates": [],
            "consolidation_groups": [],
            "cli_migration_mapping": {},
            "deprecation_candidates": [],
        }

        # Analyze by category
        category_groups = defaultdict(list)
        for script in self.scripts:
            for category in script.get("categories", []):
                category_groups[category].append(script)

        # Generate consolidation groups
        for category, scripts in category_groups.items():
            if len(scripts) > 2:  # More than 2 scripts in same category
                recommendations["consolidation_groups"].append(
                    {
                        "category": category,
                        "description": self.analyzer.categories[category][
                            "description"
                        ],
                        "scripts": [
                            {
                                "name": s["name"],
                                "path": s["path"],
                                "size": s.get("size", 0),
                                "functions": len(s.get("functions", [])),
                                "git_frequency": s.get("git_stats", {}).get(
                                    "frequency_score", 0
                                ),
                            }
                            for s in scripts
                        ],
                        "consolidation_benefit": (
                            "high" if len(scripts) > 4 else "medium"
                        ),
                    }
                )

        # CLI migration mapping
        cli_commands = {
            "test_execution": "devsynth test run",
            "coverage": "devsynth test coverage",
            "validation": "devsynth test validate",
            "test_categorization": "devsynth test analyze",
            "performance": "devsynth test benchmark",
            "reporting": "devsynth test report",
        }

        for script in self.scripts:
            for category in script.get("categories", []):
                if category in cli_commands:
                    recommendations["cli_migration_mapping"][script["name"]] = (
                        cli_commands[category]
                    )

        # Identify deprecation candidates (low usage, simple functionality)
        for script in self.scripts:
            git_stats = script.get("git_stats", {})
            if (
                git_stats.get("frequency_score", 0) < 3
                and script.get("lines", 0) < 100
                and len(script.get("functions", [])) < 3
            ):
                recommendations["deprecation_candidates"].append(
                    {
                        "name": script["name"],
                        "reason": "Low usage and simple functionality",
                        "last_modified": git_stats.get("last_modified", "unknown"),
                    }
                )

        return recommendations

    def audit(self, include_git_history: bool = False) -> Dict[str, Any]:
        """Perform complete audit of testing scripts."""
        print("Finding testing-related scripts...")
        script_paths = self.find_testing_scripts()
        print(f"Found {len(script_paths)} testing-related scripts")

        print("Analyzing scripts...")
        for script_path in script_paths:
            print(f"  Analyzing {script_path.relative_to(self.scripts_dir.parent)}...")
            script_info = self.analyzer.analyze_script(script_path)

            if include_git_history:
                script_info["git_stats"] = self.get_git_usage_frequency(script_path)

            self.scripts.append(script_info)

        print("Analyzing overlaps and generating recommendations...")
        overlaps = self.analyze_overlaps()
        recommendations = self.generate_consolidation_recommendations()

        # Generate summary statistics
        total_scripts = len(self.scripts)
        total_lines = sum(s.get("lines", 0) for s in self.scripts)
        categories_used = set()
        for script in self.scripts:
            categories_used.update(script.get("categories", []))

        return {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "scripts_directory": str(self.scripts_dir),
                "total_scripts_found": total_scripts,
                "include_git_history": include_git_history,
            },
            "summary": {
                "total_scripts": total_scripts,
                "total_lines_of_code": total_lines,
                "categories_in_use": len(categories_used),
                "average_script_size": (
                    total_lines // total_scripts if total_scripts > 0 else 0
                ),
            },
            "scripts": self.scripts,
            "overlaps": overlaps,
            "recommendations": recommendations,
            "category_definitions": self.analyzer.categories,
        }


def generate_markdown_report(audit_data: Dict[str, Any]) -> str:
    """Generate a markdown report from audit data."""
    md_lines = [
        "# Testing Scripts Audit Report",
        "",
        f"Generated on: {audit_data['metadata']['generated_at']}",
        f"Scripts directory: `{audit_data['metadata']['scripts_directory']}`",
        "",
        "## Summary",
        "",
        f"- **Total scripts analyzed**: {audit_data['summary']['total_scripts']}",
        f"- **Total lines of code**: {audit_data['summary']['total_lines_of_code']:,}",
        f"- **Categories in use**: {audit_data['summary']['categories_in_use']}",
        f"- **Average script size**: {audit_data['summary']['average_script_size']} lines",
        "",
        "## Category Breakdown",
        "",
    ]

    # Category breakdown
    category_counts = defaultdict(int)
    for script in audit_data["scripts"]:
        for category in script.get("categories", []):
            category_counts[category] += 1

    for category, count in sorted(category_counts.items()):
        description = (
            audit_data["category_definitions"].get(category, {}).get("description", "")
        )
        md_lines.append(f"- **{category}** ({count} scripts): {description}")

    # Overlaps section
    md_lines.extend(["", "## Overlapping Functionality", ""])

    overlaps = audit_data["overlaps"]
    if overlaps["category_overlaps"]:
        for category, scripts in overlaps["category_overlaps"].items():
            md_lines.append(f"### {category.replace('_', ' ').title()}")
            for script in scripts:
                md_lines.append(f"- `{script['name']}`: {script['description']}")
            md_lines.append("")
    else:
        md_lines.append("No significant overlaps detected.")

    # Recommendations section
    md_lines.extend(["", "## Consolidation Recommendations", ""])

    recs = audit_data["recommendations"]
    if recs["consolidation_groups"]:
        for group in recs["consolidation_groups"]:
            md_lines.extend(
                [
                    f"### {group['category'].replace('_', ' ').title()}",
                    f"**Benefit**: {group['consolidation_benefit']}",
                    f"**Description**: {group['description']}",
                    "**Scripts to consolidate**:",
                ]
            )
            for script in group["scripts"]:
                md_lines.append(
                    f"- `{script['name']}` ({script['size']} bytes, {script['functions']} functions)"
                )
            md_lines.append("")

    # CLI Migration section
    if recs["cli_migration_mapping"]:
        md_lines.extend(
            [
                "## CLI Migration Mapping",
                "",
                "| Current Script | Proposed CLI Command |",
                "|---------------|---------------------|",
            ]
        )
        for script, cli_cmd in recs["cli_migration_mapping"].items():
            md_lines.append(f"| `{script}` | `{cli_cmd}` |")
        md_lines.append("")

    # Deprecation candidates
    if recs["deprecation_candidates"]:
        md_lines.extend(
            [
                "## Deprecation Candidates",
                "",
                "Scripts that could be deprecated due to low usage or redundancy:",
                "",
            ]
        )
        for candidate in recs["deprecation_candidates"]:
            md_lines.append(f"- `{candidate['name']}`: {candidate['reason']}")

    return "\n".join(md_lines)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Audit testing scripts for consolidation opportunities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--scripts-dir",
        type=Path,
        default=Path("scripts"),
        help="Scripts directory to audit (default: scripts)",
    )

    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("test_reports/testing_scripts_audit.json"),
        help="Output JSON file (default: test_reports/testing_scripts_audit.json)",
    )

    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("test_reports/testing_scripts_audit.md"),
        help="Output Markdown file (default: test_reports/testing_scripts_audit.md)",
    )

    parser.add_argument(
        "--include-git-history",
        action="store_true",
        help="Include git history analysis (slower but more detailed)",
    )

    args = parser.parse_args()

    # Ensure output directory exists
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)

    # Check scripts directory exists
    if not args.scripts_dir.exists():
        print(f"Error: Scripts directory {args.scripts_dir} does not exist")
        return 1

    # Perform audit
    auditor = ScriptAuditor(args.scripts_dir)
    audit_data = auditor.audit(include_git_history=args.include_git_history)

    # Save JSON report
    with open(args.output_json, "w") as f:
        json.dump(audit_data, f, indent=2, sort_keys=True)

    # Generate and save markdown report
    markdown_report = generate_markdown_report(audit_data)
    with open(args.output_md, "w") as f:
        f.write(markdown_report)

    # Print summary
    print(f"\nAudit complete!")
    print(f"JSON report saved to: {args.output_json}")
    print(f"Markdown report saved to: {args.output_md}")

    summary = audit_data["summary"]
    print(f"\nSummary:")
    print(f"  Total scripts: {summary['total_scripts']}")
    print(f"  Total lines: {summary['total_lines_of_code']:,}")
    print(f"  Categories: {summary['categories_in_use']}")

    overlaps = audit_data["overlaps"]["overlap_summary"]
    print(f"  Categories with overlaps: {overlaps['categories_with_overlaps']}")
    print(f"  Duplicate functions: {overlaps['duplicate_function_count']}")

    recs = audit_data["recommendations"]
    print(f"  Consolidation groups identified: {len(recs['consolidation_groups'])}")
    print(f"  Scripts for CLI migration: {len(recs['cli_migration_mapping'])}")
    print(f"  Deprecation candidates: {len(recs['deprecation_candidates'])}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
