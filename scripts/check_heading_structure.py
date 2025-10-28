#!/usr/bin/env python3

"""
Script to check for and report inconsistent heading structure in Markdown files.

Usage:
    python scripts/check_heading_structure.py

This script:
1. Finds all Markdown files in the docs directory
2. Checks if each file has a single H1 heading that matches the title in the metadata
3. Checks if headings are properly nested (H1 -> H2 -> H3, not skipping levels)
4. Checks if there's a blank line before and after each heading
5. Reports any issues found
"""

import os
import re
from pathlib import Path

import yaml


def extract_metadata(content):
    """Extract metadata from the file content."""
    if not content.startswith("---"):
        return None

    # Find the end of the metadata section
    end_index = content.find("---", 3)
    if end_index == -1:
        return None

    metadata_text = content[3:end_index].strip()
    try:
        metadata = yaml.safe_load(metadata_text)
        return metadata
    except Exception as e:
        print(f"Error parsing metadata: {e}")
        return None


def extract_headings(content):
    """Extract all headings from the file content."""
    # Remove code blocks to avoid false positives
    content_without_code_blocks = re.sub(r"```.*?```", "", content, flags=re.DOTALL)

    # Find all headings
    headings = re.findall(r"^(#+)\s+(.+)$", content_without_code_blocks, re.MULTILINE)
    return [(len(h[0]), h[1].strip()) for h in headings]


def check_heading_structure(file_path):
    """Check the heading structure of a Markdown file."""
    issues = []

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Extract metadata and headings
    metadata = extract_metadata(content)
    headings = extract_headings(content)

    # Check if the file has headings
    if not headings:
        issues.append("No headings found in the file")
        return issues

    # Check if the file has a single H1 heading
    h1_headings = [h for h in headings if h[0] == 1]
    if len(h1_headings) == 0:
        issues.append("No H1 heading found")
    elif len(h1_headings) > 1:
        issues.append(
            f"Multiple H1 headings found: {', '.join([h[1] for h in h1_headings])}"
        )

    # Check if the H1 heading matches the title in the metadata
    if metadata and len(h1_headings) == 1:
        title = metadata.get("title", "").strip("\"'")
        h1_title = h1_headings[0][1]
        if title and h1_title != title:
            issues.append(
                f"H1 heading '{h1_title}' does not match metadata title '{title}'"
            )

    # Check if headings are properly nested
    current_level = 0
    for level, title in headings:
        if level > current_level + 1:
            issues.append(
                f"Heading level skipped: H{current_level} to H{level} ('{title}')"
            )
        current_level = level

    # Check if there's a blank line before and after each heading
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if re.match(r"^#+\s+", line):
            # Check if there's a blank line before the heading
            if i > 0 and lines[i - 1].strip() != "":
                issues.append(f"No blank line before heading '{line.strip()}'")

            # Check if there's a blank line after the heading
            if i < len(lines) - 1 and lines[i + 1].strip() != "":
                issues.append(f"No blank line after heading '{line.strip()}'")

    return issues


def main():
    """Main function to check heading structure in all Markdown files."""
    docs_dir = Path("docs")

    # Find all Markdown files in the docs directory
    md_files = list(docs_dir.glob("**/*.md"))
    print(f"Found {len(md_files)} Markdown files in the docs directory")

    # Check heading structure in each file
    files_with_issues = 0
    for file_path in md_files:
        try:
            issues = check_heading_structure(file_path)
            if issues:
                print(f"\nIssues in {file_path}:")
                for issue in issues:
                    print(f"  - {issue}")
                files_with_issues += 1
        except Exception as e:
            print(f"\nError processing {file_path}: {e}")
            files_with_issues += 1

    print(f"\n{files_with_issues} files have heading structure issues")


if __name__ == "__main__":
    main()
