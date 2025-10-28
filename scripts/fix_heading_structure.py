#!/usr/bin/env python3

"""
Script to fix inconsistent heading structure in Markdown files.

Usage:
    python scripts/fix_heading_structure.py

This script:
1. Finds all Markdown files in the docs directory
2. Ensures each file has a single H1 heading that matches the title in the metadata
3. Ensures headings are properly nested (H1 -> H2 -> H3, not skipping levels)
4. Ensures there's a blank line before and after each heading
5. Reports the changes made
"""

import os
import re
from pathlib import Path

import yaml


def extract_metadata(content):
    """Extract metadata from the file content."""
    if not content.startswith("---"):
        return None, content

    # Find the end of the metadata section
    end_index = content.find("---", 3)
    if end_index == -1:
        return None, content

    metadata_text = content[3:end_index].strip()
    try:
        metadata = yaml.safe_load(metadata_text)
        content_without_metadata = content[end_index + 3 :].strip()
        return metadata, content_without_metadata
    except Exception as e:
        print(f"Error parsing metadata: {e}")
        return None, content


def fix_heading_structure(file_path):
    """Fix the heading structure of a Markdown file."""
    changes = []

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Extract metadata and content
    metadata, content_without_metadata = extract_metadata(content)

    if not metadata:
        print(f"Skipping {file_path} - no metadata found")
        return changes

    # Get the title from metadata
    title = metadata.get("title", "").strip("\"'")
    if not title:
        print(f"Skipping {file_path} - no title in metadata")
        return changes

    # Split content into lines
    lines = content_without_metadata.split("\n")

    # Find the first heading
    first_heading_index = -1
    first_heading_level = 0
    first_heading_text = ""

    for i, line in enumerate(lines):
        match = re.match(r"^(#+)\s+(.+)$", line)
        if match:
            first_heading_index = i
            first_heading_level = len(match.group(1))
            first_heading_text = match.group(2).strip()
            break

    # If no heading found, add an H1 heading with the title
    if first_heading_index == -1:
        lines.insert(0, f"# {title}")
        lines.insert(1, "")
        changes.append(f"Added H1 heading '{title}'")
    # If the first heading is not H1, convert it to H1
    elif first_heading_level != 1:
        lines[first_heading_index] = f"# {first_heading_text}"
        changes.append(
            f"Converted H{first_heading_level} heading '{first_heading_text}' to H1"
        )
    # If the first heading doesn't match the title, update it
    elif first_heading_text != title:
        lines[first_heading_index] = f"# {title}"
        changes.append(f"Updated H1 heading from '{first_heading_text}' to '{title}'")

    # Ensure there's a blank line before and after each heading
    i = 0
    while i < len(lines):
        if re.match(r"^#+\s+", lines[i]):
            # Ensure blank line before heading
            if i > 0 and lines[i - 1].strip() != "":
                lines.insert(i, "")
                changes.append(
                    f"Added blank line before heading '{lines[i+1].strip()}'"
                )
                i += 1

            # Ensure blank line after heading
            if i < len(lines) - 1 and lines[i + 1].strip() != "":
                lines.insert(i + 1, "")
                changes.append(f"Added blank line after heading '{lines[i].strip()}'")
                i += 1
        i += 1

    # Remove multiple consecutive blank lines
    i = 0
    while i < len(lines) - 1:
        if lines[i].strip() == "" and lines[i + 1].strip() == "":
            lines.pop(i)
            changes.append("Removed consecutive blank line")
        else:
            i += 1

    # Ensure proper heading nesting
    current_level = 1
    i = 0
    while i < len(lines):
        match = re.match(r"^(#+)\s+(.+)$", lines[i])
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()

            # Skip the first heading (H1)
            if i > first_heading_index:
                # If heading level is skipped, adjust it
                if level > current_level + 1:
                    new_level = current_level + 1
                    lines[i] = f"{'#' * new_level} {text}"
                    changes.append(
                        f"Adjusted heading level from H{level} to H{new_level} for '{text}'"
                    )
                    level = new_level

            current_level = level
        i += 1

    # Combine metadata and fixed content
    metadata_text = "---\n" + yaml.dump(metadata, default_flow_style=False) + "---\n\n"
    fixed_content = metadata_text + "\n".join(lines)

    # Write the fixed content back to the file
    if changes:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(fixed_content)

    return changes


def main():
    """Main function to fix heading structure in all Markdown files."""
    docs_dir = Path("docs")

    # Find all Markdown files in the docs directory
    md_files = list(docs_dir.glob("**/*.md"))
    print(f"Found {len(md_files)} Markdown files in the docs directory")

    # Fix heading structure in each file
    files_fixed = 0
    for file_path in md_files:
        try:
            changes = fix_heading_structure(file_path)
            if changes:
                print(f"\nFixed {file_path}:")
                for change in changes:
                    print(f"  - {change}")
                files_fixed += 1
        except Exception as e:
            print(f"\nError processing {file_path}: {e}")

    print(f"\nFixed heading structure in {files_fixed} files")


if __name__ == "__main__":
    main()
