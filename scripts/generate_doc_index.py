#!/usr/bin/env python3
"""
Documentation Index Generation Script for DevSynth Documentation Harmonization

This script generates a comprehensive documentation index automatically by scanning
all documentation files and extracting their metadata.
"""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml


def extract_frontmatter(file_path: Path) -> tuple[dict | None, str]:
    """Extract YAML frontmatter and content from a markdown file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None, ""

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
                return frontmatter, remaining_content
        except yaml.YAMLError as e:
            print(f"YAML parsing error in {file_path}: {e}")

    return None, content


def extract_title_from_content(content: str) -> str | None:
    """Extract title from markdown content (first H1 heading)."""
    lines = content.split("\n")
    for line in lines:
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return None


def analyze_documentation_files(docs_dir: Path) -> list[dict]:
    """Analyze all markdown files in the documentation directory."""
    doc_files = []

    # Find all markdown files
    for md_file in docs_dir.rglob("*.md"):
        # Skip certain directories and files
        relative_path = md_file.relative_to(docs_dir.parent)
        relative_str = str(relative_path)

        # Skip archived content and certain generated files
        if any(
            skip in relative_str
            for skip in ["archived/", "tmp_", ".git/", "__pycache__"]
        ):
            continue

        frontmatter, content = extract_frontmatter(md_file)

        # Extract title
        title = None
        if frontmatter and "title" in frontmatter:
            title = frontmatter["title"]
        else:
            title = extract_title_from_content(content)

        if not title:
            title = md_file.stem.replace("_", " ").title()

        # Extract other metadata
        status = "unknown"
        release_phase = "unknown"
        date = "unknown"

        if frontmatter:
            status = frontmatter.get("status", "unknown")
            release_phase = frontmatter.get(
                "release_phase",
                (
                    frontmatter.get("tags", ["unknown"])[0]
                    if frontmatter.get("tags")
                    else "unknown"
                ),
            )
            date = frontmatter.get("date", frontmatter.get("last_reviewed", "unknown"))

        doc_files.append(
            {
                "path": relative_str,
                "title": title,
                "status": status,
                "release_phase": release_phase,
                "date": date,
                "size": md_file.stat().st_size,
            }
        )

    # Sort by path for consistent ordering
    doc_files.sort(key=lambda x: x["path"])
    return doc_files


def generate_index_content(doc_files: list[dict]) -> str:
    """Generate the markdown content for the documentation index."""

    # Group by top-level directory
    grouped_files = {}
    for doc_file in doc_files:
        path_parts = doc_file["path"].split("/")
        if len(path_parts) > 1 and path_parts[0] == "docs":
            if len(path_parts) > 2:
                category = path_parts[1]  # e.g., 'architecture', 'user_guides'
            else:
                category = "root"
        else:
            category = "other"

        if category not in grouped_files:
            grouped_files[category] = []
        grouped_files[category].append(doc_file)

    # Generate content
    content = f"""---
title: "Documentation Index"
date: "{datetime.now().strftime('%Y-%m-%d')}"
version: "0.1.0-alpha.1"
tags:
  - "documentation"
  - "index"
  - "generated"
status: "published"
author: "DevSynth Team"
last_reviewed: "{datetime.now().strftime('%Y-%m-%d')}"
generated: true
generator: "scripts/generate_doc_index.py"
---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; Documentation Index
</div>

# Documentation Index

_This index is automatically generated from all documentation files. Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}_

## Summary Statistics

- **Total Files**: {len(doc_files)}
- **Categories**: {len(grouped_files)}
- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

## Files by Category

"""

    # Add each category
    for category in sorted(grouped_files.keys()):
        files = grouped_files[category]
        category_title = category.replace("_", " ").title()

        content += f"\n### {category_title} ({len(files)} files)\n\n"
        content += "| File Path | Title | Status | Release Phase | Date |\n"
        content += "|-----------|-------|--------|---------------|------|\n"

        for doc_file in files:
            content += f"| {doc_file['path']} | {doc_file['title']} | {doc_file['status']} | {doc_file['release_phase']} | {doc_file['date']} |\n"

    content += f"""

## Maintenance Notes

This index is automatically generated by `scripts/generate_doc_index.py`. To update:

```bash
poetry run python scripts/generate_doc_index.py --generate
```

### Index Generation Details

- **Script**: `scripts/generate_doc_index.py`
- **Source Directory**: `docs/`
- **Output File**: `docs/documentation_index.md`
- **Excludes**: Archived content, temporary files, generated artifacts
- **Metadata Sources**: YAML frontmatter, markdown headings, file analysis

### Categories

Categories are automatically determined from the directory structure under `docs/`:

"""

    for category in sorted(grouped_files.keys()):
        files = grouped_files[category]
        content += f"- **{category.replace('_', ' ').title()}**: {len(files)} files\n"

    content += (
        "\n---\n\n*This file is automatically generated. Do not edit manually.*\n"
    )

    return content


def main():
    parser = argparse.ArgumentParser(
        description="Generate comprehensive documentation index"
    )
    parser.add_argument(
        "--generate", action="store_true", help="Generate and write the index file"
    )
    parser.add_argument(
        "--docs-dir", default="docs", help="Documentation directory to analyze"
    )
    parser.add_argument(
        "--output", default="docs/documentation_index.md", help="Output file path"
    )

    args = parser.parse_args()

    docs_dir = Path(args.docs_dir)
    if not docs_dir.exists():
        print(f"Error: Documentation directory '{docs_dir}' not found")
        sys.exit(1)

    print(f"Analyzing documentation in: {docs_dir}")
    doc_files = analyze_documentation_files(docs_dir)

    print(f"Found {len(doc_files)} documentation files")

    if args.generate:
        content = generate_index_content(doc_files)
        output_path = Path(args.output)

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ Generated documentation index: {output_path}")
            print(f"   Total files indexed: {len(doc_files)}")
        except Exception as e:
            print(f"Error writing index file: {e}")
            sys.exit(1)
    else:
        print("\nPreview of files to be indexed:")
        for doc_file in doc_files[:10]:  # Show first 10
            print(f"  {doc_file['path']} - {doc_file['title']}")
        if len(doc_files) > 10:
            print(f"  ... and {len(doc_files) - 10} more files")
        print(f"\nTo generate the index, run: python {sys.argv[0]} --generate")


if __name__ == "__main__":
    main()
