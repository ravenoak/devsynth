#!/usr/bin/env python3

"""
Script to check for broken internal links in Markdown files.

Usage:
    python scripts/check_internal_links.py

This script:
1. Finds all Markdown files in the docs directory
2. Extracts all internal links from each file
3. Checks if each link points to a valid file
4. Reports broken links
"""

import os
import re
from pathlib import Path
import urllib.parse


def slugify(text: str) -> str:
    """Convert heading text to a slug suitable for anchor comparison."""
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[\s]+", "-", text)


def anchor_exists(target_path: Path, fragment: str) -> bool:
    """Return True if the Markdown file contains a matching anchor."""
    with open(target_path, "r", encoding="utf-8") as f:
        content = f.read()

    headings = re.findall(r"^#{1,6}\s+(.*)$", content, flags=re.MULTILINE)
    return any(slugify(h) == fragment for h in headings)


def extract_internal_links(content):
    """Extract all internal links from a Markdown file."""
    # Find all Markdown links [text](url)
    link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
    links = []

    for match in re.finditer(link_pattern, content):
        link_text = match.group(1)
        link_url = match.group(2)

        # Skip external links (http://, https://, etc.)
        if re.match(r"^https?://", link_url):
            continue

        # Skip anchor links within the same file
        if link_url.startswith("#"):
            continue

        links.append((link_text, link_url))

    return links


def check_internal_links(file_path, docs_dir):
    """Check if internal links in a file point to valid files."""
    broken_links = []

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract internal links
    links = extract_internal_links(content)

    # Check each link
    for link_text, link_url in links:
        # Decode URL-encoded characters and separate fragment
        link_url = urllib.parse.unquote(link_url)
        parsed = urllib.parse.urlparse(link_url)
        link_path, fragment = parsed.path, parsed.fragment

        # Handle relative paths
        if link_path.startswith("/"):
            # Absolute path from repo root
            target_path = docs_dir.parent / link_path.lstrip("/")
        else:
            # Relative path from current file
            target_path = file_path.parent / link_path

        # Normalize path
        target_path = target_path.resolve()

        # Check if the target file exists
        if not target_path.exists():
            broken_links.append(
                {
                    "text": link_text,
                    "url": link_url,
                    "target_path": str(target_path),
                }
            )
            continue

        # Verify that the fragment exists in the target file
        if fragment and not anchor_exists(target_path, fragment):
            broken_links.append(
                {
                    "text": link_text,
                    "url": link_url,
                    "target_path": f"{target_path}#{fragment}",
                }
            )

    return broken_links


def main():
    """Main function to check internal links in all Markdown files."""
    docs_dir = Path("docs")

    # Find all Markdown files in the docs directory
    md_files = list(docs_dir.glob("**/*.md"))
    print(f"Found {len(md_files)} Markdown files in the docs directory")

    # Check internal links in each file
    files_with_broken_links = 0
    total_broken_links = 0

    for file_path in md_files:
        try:
            broken_links = check_internal_links(file_path, docs_dir)
            if broken_links:
                print(f"\nBroken links in {file_path}:")
                for link in broken_links:
                    print(
                        f"  - [{link['text']}]({link['url']}) -> {link['target_path']}"
                    )
                files_with_broken_links += 1
                total_broken_links += len(broken_links)
        except Exception as e:
            print(f"\nError processing {file_path}: {e}")

    print(
        f"\nFound {total_broken_links} broken links in {files_with_broken_links} files"
    )


if __name__ == "__main__":
    main()
