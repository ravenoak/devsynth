#!/usr/bin/env python3

"""
Script to add metadata headers to Markdown files in the docs directory that are missing them.

Usage:
    python scripts/add_metadata_headers.py

This script:
1. Finds all Markdown files in the docs directory
2. Checks if each file has a metadata header
3. If not, extracts the title from the first heading
4. Generates appropriate tags based on the file path
5. Adds a metadata header with the current date, version 1.0.0, appropriate tags,
   status "published", author "DevSynth Team", and last_reviewed as the current date
"""

import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

# Get the current date in YYYY-MM-DD format
CURRENT_DATE = datetime.now().strftime("%Y-%m-%d")


def has_metadata_header(content):
    """Check if the file has a metadata header."""
    return content.startswith("---")


def extract_title(content):
    """Extract the title from the first heading in the file."""
    # Look for the first heading (# Title)
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return "Untitled Document"


def generate_tags(file_path):
    """Generate appropriate tags based on the file path."""
    tags = []

    # Add tags based on directory
    parts = file_path.parts
    if "getting_started" in parts:
        tags.append("getting-started")
    if "user_guides" in parts:
        tags.append("user-guide")
    if "developer_guides" in parts:
        tags.append("developer-guide")
    if "architecture" in parts:
        tags.append("architecture")
    if "technical_reference" in parts:
        tags.append("technical-reference")
    if "analysis" in parts:
        tags.append("analysis")
    if "implementation" in parts:
        tags.append("implementation")
    if "specifications" in parts:
        tags.append("specification")
    if "roadmap" in parts:
        tags.append("roadmap")
    if "policies" in parts:
        tags.append("policy")

    # Add tags based on filename
    filename = file_path.stem.lower()
    if "cli" in filename:
        tags.append("cli")
    if "api" in filename:
        tags.append("api")
    if "reference" in filename:
        tags.append("reference")
    if "guide" in filename:
        tags.append("guide")
    if "tutorial" in filename:
        tags.append("tutorial")
    if "overview" in filename:
        tags.append("overview")
    if "installation" in filename:
        tags.append("installation")
    if "configuration" in filename:
        tags.append("configuration")
    if "troubleshooting" in filename:
        tags.append("troubleshooting")

    # Ensure we have at least one tag
    if not tags:
        tags.append("documentation")

    return tags


def create_metadata_header(title, tags):
    """Create a metadata header with the given title and tags."""
    tags_str = "\n  - ".join([f'"{tag}"' for tag in tags])

    return f"""---
title: "{title}"
date: "{CURRENT_DATE}"
version: "0.1.0-alpha.1"
tags:
  - {tags_str}
status: "published"
author: "DevSynth Team"
last_reviewed: "{CURRENT_DATE}"
---

"""


def add_metadata_header(file_path):
    """Add a metadata header to the file if it doesn't have one."""
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    if has_metadata_header(content):
        print(f"Skipping {file_path} - already has metadata header")
        return

    title = extract_title(content)
    tags = generate_tags(file_path)
    header = create_metadata_header(title, tags)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(header + content)

    print(f"Added metadata header to {file_path}")


def main():
    """Main function to add metadata headers to all Markdown files in the docs directory."""
    docs_dir = Path("docs")

    # Find all Markdown files in the docs directory
    md_files = list(docs_dir.glob("**/*.md"))
    print(f"Found {len(md_files)} Markdown files in the docs directory")

    # Add metadata headers to files missing them
    files_updated = 0
    for file_path in md_files:
        try:
            add_metadata_header(file_path)
            files_updated += 1
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    print(f"Updated {files_updated} files with metadata headers")


if __name__ == "__main__":
    main()
