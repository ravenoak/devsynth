#!/usr/bin/env python3
"""
Terminology Analysis Script for DevSynth Documentation Harmonization

This script analyzes terminology usage across documentation to identify
inconsistencies and ensure alignment with the project glossary.
"""

import argparse
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple


def extract_terms_from_content(content: str) -> set[str]:
    """Extract potential technical terms from content."""
    # Common DevSynth terms to look for
    devsynth_terms = {
        "EDRR",
        "WSDE",
        "DevSynth",
        "dialectical reasoning",
        "hexagonal architecture",
        "memory store",
        "provider system",
        "agent system",
        "BDD",
        "TDD",
        "requirements traceability",
        "consensus building",
        "peer review",
        "MVUU",
        "UXBridge",
        "CLI",
        "WebUI",
        "API",
        "specification",
        "implementation",
        "validation",
        "harmonization",
    }

    found_terms = set()
    content_lower = content.lower()

    for term in devsynth_terms:
        if term.lower() in content_lower:
            found_terms.add(term)

    # Look for capitalized technical terms (likely acronyms or proper nouns)
    acronym_pattern = r"\b[A-Z]{2,}\b"
    acronyms = re.findall(acronym_pattern, content)
    found_terms.update(acronyms)

    return found_terms


def load_glossary_terms(glossary_path: Path) -> dict[str, str]:
    """Load terms and definitions from the glossary file."""
    glossary_terms = {}

    if not glossary_path.exists():
        print(f"Warning: Glossary file not found at {glossary_path}")
        return glossary_terms

    try:
        with open(glossary_path, encoding="utf-8") as f:
            content = f.read()

        # Look for term definitions (markdown format: **Term**: Definition)
        term_pattern = r"\*\*([^*]+)\*\*:\s*([^\n]+)"
        matches = re.findall(term_pattern, content)

        for term, definition in matches:
            glossary_terms[term.strip()] = definition.strip()

    except Exception as e:
        print(f"Error reading glossary: {e}")

    return glossary_terms


def analyze_terminology_usage(docs_dir: Path, glossary_path: Path) -> dict:
    """Analyze terminology usage across all documentation."""
    results = {
        "files_processed": 0,
        "terms_found": Counter(),
        "files_by_term": defaultdict(list),
        "undefined_terms": set(),
        "glossary_terms": {},
        "coverage_analysis": {},
    }

    # Load glossary
    results["glossary_terms"] = load_glossary_terms(glossary_path)
    glossary_terms_lower = {
        term.lower(): term for term in results["glossary_terms"].keys()
    }

    # Analyze all markdown files
    for md_file in docs_dir.rglob("*.md"):
        # Skip archived content and certain files
        if any(skip in str(md_file) for skip in ["archived/", "tmp_", ".git/"]):
            continue

        results["files_processed"] += 1

        try:
            with open(md_file, encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            continue

        # Extract terms from this file
        file_terms = extract_terms_from_content(content)

        for term in file_terms:
            results["terms_found"][term] += 1
            results["files_by_term"][term].append(
                str(md_file.relative_to(docs_dir.parent))
            )

            # Check if term is in glossary
            if term.lower() not in glossary_terms_lower:
                results["undefined_terms"].add(term)

    # Analyze coverage
    total_terms = len(results["terms_found"])
    defined_terms = total_terms - len(results["undefined_terms"])
    results["coverage_analysis"] = {
        "total_terms_found": total_terms,
        "defined_in_glossary": defined_terms,
        "undefined_terms": len(results["undefined_terms"]),
        "coverage_percentage": (
            (defined_terms / total_terms * 100) if total_terms > 0 else 0
        ),
    }

    return results


def generate_terminology_report(results: dict) -> str:
    """Generate comprehensive terminology analysis report."""
    coverage = results["coverage_analysis"]

    report = f"""
TERMINOLOGY ANALYSIS REPORT
{'=' * 50}

Summary:
- Files processed: {results['files_processed']}
- Unique terms found: {coverage['total_terms_found']}
- Terms defined in glossary: {coverage['defined_in_glossary']}
- Undefined terms: {coverage['undefined_terms']}
- Glossary coverage: {coverage['coverage_percentage']:.1f}%

"""

    # Most frequently used terms
    if results["terms_found"]:
        report += "Most Frequently Used Terms:\n"
        report += "-" * 30 + "\n"
        for term, count in results["terms_found"].most_common(10):
            status = (
                "✅"
                if term.lower() in [t.lower() for t in results["glossary_terms"].keys()]
                else "❌"
            )
            report += f"{status} {term}: {count} occurrences\n"
        report += "\n"

    # Undefined terms that should be in glossary
    if results["undefined_terms"]:
        undefined_list = sorted(results["undefined_terms"])
        report += f"Undefined Terms Needing Glossary Entries ({len(undefined_list)}):\n"
        report += "-" * 40 + "\n"
        for term in undefined_list[:20]:  # Show first 20
            count = results["terms_found"][term]
            report += f"- {term} ({count} occurrences)\n"

        if len(undefined_list) > 20:
            report += f"... and {len(undefined_list) - 20} more undefined terms\n"
        report += "\n"

    # Terms with high usage that should be prioritized
    high_usage_undefined = [
        (term, count)
        for term, count in results["terms_found"].most_common()
        if term in results["undefined_terms"] and count >= 5
    ]

    if high_usage_undefined:
        report += "High-Priority Terms for Glossary (5+ occurrences):\n"
        report += "-" * 45 + "\n"
        for term, count in high_usage_undefined:
            report += f"🔥 {term}: {count} occurrences\n"
        report += "\n"

    report += "=" * 50 + "\n"
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Analyze terminology usage in documentation"
    )
    parser.add_argument(
        "--docs-dir", default="docs", help="Documentation directory to analyze"
    )
    parser.add_argument(
        "--glossary", default="docs/glossary.md", help="Glossary file path"
    )
    parser.add_argument("--report-file", help="Save report to file")

    args = parser.parse_args()

    docs_dir = Path(args.docs_dir)
    glossary_path = Path(args.glossary)

    if not docs_dir.exists():
        print(f"Error: Documentation directory '{docs_dir}' not found")
        sys.exit(1)

    print(f"Analyzing terminology in: {docs_dir}")
    print(f"Using glossary: {glossary_path}")

    results = analyze_terminology_usage(docs_dir, glossary_path)
    report = generate_terminology_report(results)

    print(report)

    if args.report_file:
        try:
            with open(args.report_file, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"Report saved to: {args.report_file}")
        except Exception as e:
            print(f"Error saving report: {e}")


if __name__ == "__main__":
    main()
