#!/usr/bin/env python3

"""
Script to check for inconsistent terminology usage in Markdown files.

Usage:
    python scripts/check_terminology.py

This script:
1. Extracts terms and their preferred forms from the glossary
2. Searches for variations of these terms in the documentation
3. Reports inconsistencies
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


def extract_terms_from_glossary(glossary_path):
    """Extract terms and their definitions from the glossary."""
    terms = {}

    with open(glossary_path, encoding="utf-8") as f:
        content = f.read()

    # Extract term headings (### Term)
    term_matches = re.finditer(r"###\s+([^\n]+)", content)
    for match in term_matches:
        term = match.group(1).strip()
        terms[term] = term

    return terms


def check_terminology(file_path, terminology_mapping, glossary_terms):
    """Check for inconsistent terminology usage in a Markdown file."""
    inconsistencies = []

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Skip the glossary itself
    if file_path.name == "glossary.md":
        return inconsistencies

    # Check for variations of terms
    for term, (preferred_form, variations) in terminology_mapping.items():
        for variation in variations:
            # Only check for variations that are different from the preferred form
            if variation.lower() != preferred_form.lower():
                # Use word boundary to avoid partial matches
                pattern = r"\b" + re.escape(variation) + r"\b"
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Skip matches in code blocks
                    code_block_start = content.rfind("```", 0, match.start())
                    code_block_end = content.rfind("```", 0, match.start())
                    if code_block_start > code_block_end:
                        continue

                    inconsistencies.append(
                        {
                            "term": term,
                            "preferred_form": preferred_form,
                            "found": match.group(0),
                            "context": content[
                                max(0, match.start() - 50) : match.end() + 50
                            ],
                        }
                    )

    # Check for capitalization issues
    for term, correct_capitalization in CAPITALIZATION_RULES.items():
        pattern = r"\b" + re.escape(term) + r"\b"
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            found = match.group(0)
            if found != correct_capitalization:
                # Skip matches in code blocks
                code_block_start = content.rfind("```", 0, match.start())
                code_block_end = content.rfind("```", 0, match.start())
                if code_block_start > code_block_end:
                    continue

                inconsistencies.append(
                    {
                        "term": term,
                        "preferred_form": correct_capitalization,
                        "found": found,
                        "context": content[
                            max(0, match.start() - 50) : match.end() + 50
                        ],
                    }
                )

    return inconsistencies


def main():
    """Main function to check terminology in all Markdown files."""
    docs_dir = Path("docs")
    glossary_path = docs_dir / "glossary.md"

    # Extract terms from glossary
    glossary_terms = extract_terms_from_glossary(glossary_path)

    # Find all Markdown files in the docs directory
    md_files = list(docs_dir.glob("**/*.md"))
    print(f"Found {len(md_files)} Markdown files in the docs directory")

    # Check terminology in each file
    files_with_issues = 0
    total_inconsistencies = 0

    for file_path in md_files:
        try:
            inconsistencies = check_terminology(
                file_path, TERMINOLOGY_MAPPING, glossary_terms
            )
            if inconsistencies:
                print(f"\nInconsistent terminology in {file_path}:")
                for issue in inconsistencies:
                    print(
                        f"  - Found '{issue['found']}' instead of '{issue['preferred_form']}'"
                    )
                    print(f"    Context: ...{issue['context'].strip()}...")
                files_with_issues += 1
                total_inconsistencies += len(inconsistencies)
        except Exception as e:
            print(f"\nError processing {file_path}: {e}")

    print(
        f"\nFound {total_inconsistencies} terminology inconsistencies in {files_with_issues} files"
    )


if __name__ == "__main__":
    main()
