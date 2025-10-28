#!/usr/bin/env python3
"""
Internal Link Validation Script for DevSynth Documentation Harmonization

This script validates all internal links within the documentation to ensure
they remain valid after harmonization changes.
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from urllib.parse import unquote, urlparse


def find_markdown_links(content: str) -> list[tuple[str, str]]:
    """Find all markdown links in content. Returns list of (text, url) tuples."""
    # Pattern for markdown links: [text](url)
    link_pattern = r"\[([^\]]*)\]\(([^)]+)\)"
    matches = re.findall(link_pattern, content)
    return matches


def find_html_links(content: str) -> list[str]:
    """Find all HTML href links in content."""
    # Pattern for HTML links: href="url"
    href_pattern = r'href=["\']([^"\']+)["\']'
    matches = re.findall(href_pattern, content)
    return matches


def is_internal_link(url: str) -> bool:
    """Check if a URL is an internal link (relative path)."""
    parsed = urlparse(url)
    # Internal links have no scheme and no netloc
    return not parsed.scheme and not parsed.netloc and not url.startswith("#")


def resolve_link_path(source_file: Path, link_url: str) -> Path:
    """Resolve a relative link URL to an absolute path."""
    # Remove anchor fragments
    url_without_anchor = link_url.split("#")[0]
    if not url_without_anchor:
        return source_file  # Just an anchor link to same file

    # Decode URL encoding
    url_without_anchor = unquote(url_without_anchor)

    # Resolve relative to source file's directory
    source_dir = source_file.parent
    resolved = (source_dir / url_without_anchor).resolve()
    return resolved


def validate_documentation_links(docs_dir: Path) -> dict[str, list[dict]]:
    """Validate all internal links in documentation files."""
    results = {
        "valid_links": [],
        "broken_links": [],
        "files_processed": 0,
        "total_links_checked": 0,
    }

    # Find all markdown files
    for md_file in docs_dir.rglob("*.md"):
        # Skip archived content
        if "archived/" in str(md_file):
            continue

        results["files_processed"] += 1

        try:
            with open(md_file, encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            results["broken_links"].append(
                {
                    "source_file": str(md_file),
                    "error": f"Could not read file: {e}",
                    "link_url": None,
                    "link_text": None,
                }
            )
            continue

        # Find markdown links
        md_links = find_markdown_links(content)
        html_links = find_html_links(content)

        # Check each markdown link
        for link_text, link_url in md_links:
            if is_internal_link(link_url):
                results["total_links_checked"] += 1
                target_path = resolve_link_path(md_file, link_url)

                if target_path.exists():
                    try:
                        target_rel = str(target_path.relative_to(docs_dir.parent))
                    except ValueError:
                        target_rel = str(target_path)
                    results["valid_links"].append(
                        {
                            "source_file": str(md_file.relative_to(docs_dir.parent)),
                            "link_text": link_text,
                            "link_url": link_url,
                            "target_path": target_rel,
                        }
                    )
                else:
                    results["broken_links"].append(
                        {
                            "source_file": str(md_file.relative_to(docs_dir.parent)),
                            "link_text": link_text,
                            "link_url": link_url,
                            "target_path": str(target_path),
                            "error": "Target file does not exist",
                        }
                    )

        # Check HTML links (like breadcrumbs)
        for link_url in html_links:
            if is_internal_link(link_url):
                results["total_links_checked"] += 1
                target_path = resolve_link_path(md_file, link_url)

                if target_path.exists():
                    try:
                        target_rel = str(target_path.relative_to(docs_dir.parent))
                    except ValueError:
                        target_rel = str(target_path)
                    results["valid_links"].append(
                        {
                            "source_file": str(md_file.relative_to(docs_dir.parent)),
                            "link_text": "HTML link",
                            "link_url": link_url,
                            "target_path": target_rel,
                        }
                    )
                else:
                    results["broken_links"].append(
                        {
                            "source_file": str(md_file.relative_to(docs_dir.parent)),
                            "link_text": "HTML link",
                            "link_url": link_url,
                            "target_path": str(target_path),
                            "error": "Target file does not exist",
                        }
                    )

    return results


def generate_validation_report(results: dict) -> str:
    """Generate a validation report from results."""
    total_links = results["total_links_checked"]
    valid_links = len(results["valid_links"])
    broken_links = len(results["broken_links"])

    if total_links > 0:
        success_rate = (valid_links / total_links) * 100
    else:
        success_rate = 0

    report = f"""
INTERNAL LINK VALIDATION REPORT
{'=' * 50}

Summary:
- Files processed: {results['files_processed']}
- Total internal links checked: {total_links}
- Valid links: {valid_links}
- Broken links: {broken_links}
- Success rate: {success_rate:.1f}%

"""

    if broken_links > 0:
        report += f"BROKEN LINKS ({broken_links}):\n"
        report += "-" * 30 + "\n"

        for broken in results["broken_links"][:20]:  # Show first 20
            report += f"\n📁 {broken['source_file']}\n"
            if broken["link_text"]:
                report += f"   Text: {broken['link_text']}\n"
            report += f"   URL: {broken['link_url']}\n"
            report += f"   Error: {broken['error']}\n"

        if broken_links > 20:
            report += f"\n... and {broken_links - 20} more broken links\n"
    else:
        report += "✅ ALL INTERNAL LINKS ARE VALID!\n"

    report += "\n" + "=" * 50 + "\n"

    return report


def main():
    parser = argparse.ArgumentParser(
        description="Validate internal links in documentation"
    )
    parser.add_argument(
        "--docs-dir", default="docs", help="Documentation directory to validate"
    )
    parser.add_argument("--report-file", help="Save report to file")

    args = parser.parse_args()

    docs_dir = Path(args.docs_dir)
    if not docs_dir.exists():
        print(f"Error: Documentation directory '{docs_dir}' not found")
        sys.exit(1)

    print(f"Validating internal links in: {docs_dir}")
    results = validate_documentation_links(docs_dir)

    report = generate_validation_report(results)
    print(report)

    if args.report_file:
        try:
            with open(args.report_file, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"Report saved to: {args.report_file}")
        except Exception as e:
            print(f"Error saving report: {e}")

    # Exit with error code if there are broken links
    if len(results["broken_links"]) > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
