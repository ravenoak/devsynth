#!/usr/bin/env python3
"""
Script to add breadcrumb navigation to Markdown files in the docs directory.

This script scans all Markdown files in the docs directory and adds breadcrumb
navigation at the top of each file, showing the hierarchical path from the root
to the current document.
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Regular expression to match YAML frontmatter
FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
# Regular expression to match YAML frontmatter with closing --- on the same line
INVALID_FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)---\s*\n", re.DOTALL)

# Regular expression to match the title in frontmatter
TITLE_PATTERN = re.compile(r'title:\s*"?([^"\n]+)"?')

# Current date for updating "last_reviewed" dates
CURRENT_DATE = datetime.now().strftime("%Y-%m-%d")


def get_breadcrumb_path(file_path, docs_dir):
    """
    Generate the breadcrumb path for a file.

    Args:
        file_path: The path to the file
        docs_dir: The root docs directory

    Returns:
        A list of (name, path) tuples representing the breadcrumb path
    """
    rel_path = os.path.relpath(file_path, docs_dir)
    path_parts = rel_path.split(os.sep)

    # Remove the filename from the path parts
    path_parts = path_parts[:-1]

    # Start with the root
    breadcrumbs = [("Documentation", "../index.md")]

    # Build the breadcrumb path
    current_path = ""
    for part in path_parts:
        current_path = os.path.join(current_path, part)
        index_path = os.path.join(docs_dir, current_path, "index.md")

        # Use the directory name as the breadcrumb name
        name = part.replace("_", " ").title()

        # If there's an index.md file, use it as the path
        if os.path.exists(index_path):
            rel_index_path = os.path.relpath(index_path, os.path.dirname(file_path))
            breadcrumbs.append((name, rel_index_path))
        else:
            # Otherwise, just use the name without a link
            breadcrumbs.append((name, None))

    return breadcrumbs


def get_file_title(content):
    """
    Extract the title from the frontmatter of a Markdown file.

    Args:
        content: The content of the Markdown file

    Returns:
        The title if found, None otherwise
    """
    frontmatter_match = FRONTMATTER_PATTERN.search(content)
    if frontmatter_match:
        frontmatter = frontmatter_match.group(1)
        title_match = TITLE_PATTERN.search(frontmatter)
        if title_match:
            return title_match.group(1)

    return None


def add_breadcrumb_navigation(file_path, docs_dir):
    """
    Add breadcrumb navigation to a Markdown file.

    Args:
        file_path: The path to the file
        docs_dir: The root docs directory

    Returns:
        True if the file was updated, False otherwise
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Make a copy of the original content for comparison
        original_content = content

        # Extract the frontmatter
        frontmatter_match = FRONTMATTER_PATTERN.search(content)
        invalid_frontmatter_match = INVALID_FRONTMATTER_PATTERN.search(content)

        if frontmatter_match:
            # Standard frontmatter with proper formatting
            frontmatter = frontmatter_match.group(1)
        elif invalid_frontmatter_match:
            # Frontmatter with closing --- on the same line
            frontmatter = invalid_frontmatter_match.group(1)
            # Fix the frontmatter by ensuring the closing --- is on a separate line
            content = content.replace(frontmatter + "---", frontmatter + "\n---")
        else:
            print(f"Warning: No frontmatter found in {file_path}", file=sys.stderr)
            return False

        # Get the title from the frontmatter
        title = get_file_title(content)
        if not title:
            print(f"Warning: No title found in {file_path}", file=sys.stderr)
            return False

        # Generate the breadcrumb path
        breadcrumbs = get_breadcrumb_path(file_path, docs_dir)

        # Add the current page to the breadcrumbs
        breadcrumbs.append((title, None))

        # Generate the breadcrumb HTML
        breadcrumb_html = '<div class="breadcrumbs">\n'
        for i, (name, path) in enumerate(breadcrumbs):
            if i > 0:
                breadcrumb_html += " &gt; "

            if path:
                breadcrumb_html += f'<a href="{path}">{name}</a>'
            else:
                breadcrumb_html += name

        breadcrumb_html += "\n</div>\n\n"

        # Add the breadcrumb navigation after the frontmatter
        if frontmatter_match:
            content = FRONTMATTER_PATTERN.sub(
                f"---\n{frontmatter}---\n\n{breadcrumb_html}", content
            )
        elif invalid_frontmatter_match:
            content = INVALID_FRONTMATTER_PATTERN.sub(
                f"---\n{frontmatter}\n---\n\n{breadcrumb_html}", content
            )

        # Check if any changes were made
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True

        return False

    except Exception as e:
        print(f"Error updating {file_path}: {e}", file=sys.stderr)
        return False


def update_files_in_directory(root_dir):
    """
    Add breadcrumb navigation to all Markdown files in the given directory and its subdirectories.

    Args:
        root_dir: The root directory to scan

    Returns:
        A tuple of (updated_files, error_files)
    """
    updated_files = []
    error_files = []

    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                try:
                    if add_breadcrumb_navigation(file_path, root_dir):
                        updated_files.append(file_path)
                except Exception as e:
                    print(f"Error updating {file_path}: {e}", file=sys.stderr)
                    error_files.append(file_path)

    return updated_files, error_files


def main():
    """Main function."""
    docs_dir = Path(__file__).parent.parent / "docs"

    print(f"Adding breadcrumb navigation to Markdown files in {docs_dir}...")
    updated_files, error_files = update_files_in_directory(docs_dir)

    if not updated_files and not error_files:
        print("No Markdown files were updated.")
        return

    if updated_files:
        print(f"Added breadcrumb navigation to {len(updated_files)} Markdown files:")
        for file_path in updated_files:
            rel_path = os.path.relpath(file_path, Path(__file__).parent.parent)
            print(f"- {rel_path}")

    if error_files:
        print(f"Failed to update {len(error_files)} Markdown files:")
        for file_path in error_files:
            rel_path = os.path.relpath(file_path, Path(__file__).parent.parent)
            print(f"- {rel_path}")


if __name__ == "__main__":
    main()
