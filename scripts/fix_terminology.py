#!/usr/bin/env python3

"""
Script to fix inconsistent terminology usage in Markdown files.

Usage:
    python scripts/fix_terminology.py

This script:
1. Uses the same terminology mapping as the check_terminology.py script
2. Replaces variations of terms with their preferred forms
3. Fixes capitalization issues
4. Reports the changes made
"""

import os
import re
from pathlib import Path

import yaml

# Define terms and their variations to check
TERMINOLOGY_MAPPING = {
    # Term: [preferred form, [variations to check]]
    "EDRR": [
        "EDRR",
        ["EDRR cycle", "edrr", "E-D-R-R", "Expand-Differentiate-Refine-Retrospect"],
    ],
    "WSDE": ["WSDE", ["wsde", "W-S-D-E", "Worker Self-Directed Enterprise"]],
    "Project Configuration": [
        "Project Configuration",
        ["manifest.yaml", "devsynth.yaml", "project manifest", "project yaml"],
    ],
    "Dialectical Reasoning": [
        "Dialectical Reasoning",
        ["dialectical reasoning", "dialectic reasoning", "dialectics"],
    ],
    "Hexagonal Architecture": [
        "Hexagonal Architecture",
        [
            "hexagonal architecture",
            "ports and adapters",
            "ports and adapters architecture",
        ],
    ],
    "Memory System": [
        "Memory System",
        ["memory system", "memory subsystem", "memory management system"],
    ],
    "Provider": [
        "Provider",
        ["LLM provider", "language model provider", "model provider"],
    ],
    "Adapter": ["Adapter", ["adapter", "adaptor"]],
    "Port": ["Port", ["port", "interface port"]],
    "Agent": ["Agent", ["agent", "AI agent", "LLM agent"]],
    "Embedding": ["Embedding", ["embedding", "vector embedding", "text embedding"]],
    "ChromaDB": ["ChromaDB", ["chromadb", "Chroma DB", "chroma db"]],
    "Kuzu": ["Kuzu", ["kuzu", "KuzuDB", "kuzu db"]],
    "TinyDB": ["TinyDB", ["tinydb", "Tiny DB", "tiny db"]],
    "RDFLib": ["RDFLib", ["rdflib", "RDF Lib", "rdf lib"]],
}

# Define terms that should always be capitalized in a specific way
CAPITALIZATION_RULES = {
    "EDRR": "EDRR",
    "WSDE": "WSDE",
    "ChromaDB": "ChromaDB",
    "TinyDB": "TinyDB",
    "RDFLib": "RDFLib",
    "Kuzu": "Kuzu",
}


def fix_terminology(file_path):
    """Fix inconsistent terminology usage in a Markdown file."""
    changes = []

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Skip the glossary itself
    if file_path.name == "glossary.md":
        return changes, content

    # Fix variations of terms
    for term, (preferred_form, variations) in TERMINOLOGY_MAPPING.items():
        for variation in variations:
            # Only fix variations that are different from the preferred form
            if variation.lower() != preferred_form.lower():
                # Use word boundary to avoid partial matches
                pattern = r"\b" + re.escape(variation) + r"\b"

                # Find all matches
                matches = list(re.finditer(pattern, content, re.IGNORECASE))

                # Process matches in reverse order to avoid index issues
                for match in reversed(matches):
                    # Skip matches in code blocks
                    code_block_start = content.rfind("```", 0, match.start())
                    code_block_end = content.rfind("```", 0, match.start())
                    if code_block_start > code_block_end:
                        continue

                    # Replace the variation with the preferred form
                    found = match.group(0)
                    content = (
                        content[: match.start()]
                        + preferred_form
                        + content[match.end() :]
                    )
                    changes.append(f"Replaced '{found}' with '{preferred_form}'")

    # Fix capitalization issues
    for term, correct_capitalization in CAPITALIZATION_RULES.items():
        pattern = r"\b" + re.escape(term) + r"\b"

        # Find all matches
        matches = list(re.finditer(pattern, content, re.IGNORECASE))

        # Process matches in reverse order to avoid index issues
        for match in reversed(matches):
            found = match.group(0)
            if found != correct_capitalization:
                # Skip matches in code blocks
                code_block_start = content.rfind("```", 0, match.start())
                code_block_end = content.rfind("```", 0, match.start())
                if code_block_start > code_block_end:
                    continue

                # Replace with correct capitalization
                content = (
                    content[: match.start()]
                    + correct_capitalization
                    + content[match.end() :]
                )
                changes.append(
                    f"Fixed capitalization: '{found}' -> '{correct_capitalization}'"
                )

    return changes, content


def main():
    """Main function to fix terminology in all Markdown files."""
    docs_dir = Path("docs")

    # Find all Markdown files in the docs directory
    md_files = list(docs_dir.glob("**/*.md"))
    print(f"Found {len(md_files)} Markdown files in the docs directory")

    # Fix terminology in each file
    files_fixed = 0
    total_changes = 0

    for file_path in md_files:
        try:
            changes, fixed_content = fix_terminology(file_path)
            if changes:
                # Write the fixed content back to the file
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(fixed_content)

                print(f"\nFixed {file_path}:")
                for change in changes:
                    print(f"  - {change}")
                files_fixed += 1
                total_changes += len(changes)
        except Exception as e:
            print(f"\nError processing {file_path}: {e}")

    print(f"\nMade {total_changes} terminology changes in {files_fixed} files")


if __name__ == "__main__":
    main()
