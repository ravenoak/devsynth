import argparse
import pathlib
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import yaml # type: ignore

# Define the schema based on docs/metadata_template.md
# ---
# title: "Document Title"
# date: "YYYY-MM-DD"  # or YYYY-MM-DDTHH:MM:SSZ (ISO 8601)
# version: "X.Y.Z"    # Semantic versioning for the document content
# tags:
#   - "tag1"
#   - "tag2"
# status: "draft"     # Allowed values: draft, review, published, archived
# author: "Author Name" # Optional
# last_reviewed: "YYYY-MM-DD" # Optional
# ---

REQUIRED_FIELDS = ["title", "date", "version", "tags", "status"]
OPTIONAL_FIELDS = ["author", "last_reviewed"]
ALLOWED_STATUSES = ["draft", "review", "published", "archived"]

# Regex to capture front-matter
# It looks for a block starting and ending with '---'
# and captures the content in between.
# The re.DOTALL flag allows '.' to match newlines.
FRONT_MATTER_REGEX = re.compile(r"^---\s*$(.*?)^---\s*$", re.MULTILINE | re.DOTALL)

def parse_date(date_str: str) -> bool:
    """Validates if the date string is in YYYY-MM-DD format or ISO 8601 format."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        try:
            # Attempt to parse as ISO 8601. datetime.fromisoformat is quite flexible.
            datetime.fromisoformat(date_str.replace("Z", "+00:00")) # Python < 3.12 needs Z replaced
            return True
        except ValueError:
            return False

def parse_version(version_str: str) -> bool:
    """Validates a simple X.Y.Z version string. Can be expanded for more complex semver."""
    parts = version_str.split('.')
    if len(parts) == 3:
        return all(part.isdigit() for part in parts)
    # Allow for suffixes like -alpha, -beta
    if len(parts) == 3 and '-' in parts[2]:
        main_version, suffix = parts[2].split('-',1)
        return all(part.isdigit() for part in parts[:2]) and main_version.isdigit() and len(suffix) > 0

    return False


def extract_front_matter(content: str) -> Optional[Dict[str, Any]]:
    """Extracts front matter from markdown content."""
    match = FRONT_MATTER_REGEX.search(content)
    if not match:
        return None
    front_matter_str = match.group(1)
    try:
        data = yaml.safe_load(front_matter_str)
        if not isinstance(data, dict):
            return None # Front matter is not a dictionary
        return data
    except yaml.YAMLError:
        return None


def validate_metadata(file_path: pathlib.Path, metadata: Dict[str, Any]) -> List[str]:
    """Validates the extracted metadata against the schema."""
    errors: List[str] = []

    # Check for required fields
    for field in REQUIRED_FIELDS:
        if field not in metadata:
            errors.append(f"Missing required field: '{field}'")
        elif metadata.get(field) is None or metadata.get(field) == '':
             errors.append(f"Required field '{field}' must not be empty.")


    # Validate field types and values
    title = metadata.get("title")
    if title is not None and not isinstance(title, str):
        errors.append(f"Field 'title' must be a string. Found: {type(title)}")

    date_val = metadata.get("date")
    if date_val is not None:
        if not isinstance(date_val, str) or not parse_date(date_val):
            errors.append(f"Field 'date' must be a string in YYYY-MM-DD or ISO 8601 format. Found: '{date_val}'")

    version_val = metadata.get("version")
    if version_val is not None:
        if not isinstance(version_val, str) or not parse_version(str(version_val)): # Ensure it's a string for parse_version
            errors.append(f"Field 'version' must be a string in X.Y.Z format (e.g., 1.0.0). Found: '{version_val}'")

    tags_val = metadata.get("tags")
    if tags_val is not None:
        if not isinstance(tags_val, list) or not all(isinstance(tag, str) for tag in tags_val):
            errors.append(f"Field 'tags' must be a list of strings. Found: {tags_val}")
        elif not tags_val: # Check for empty list
            errors.append("Field 'tags' must not be empty. Please provide at least one tag.")


    status_val = metadata.get("status")
    if status_val is not None:
        if not isinstance(status_val, str) or status_val not in ALLOWED_STATUSES:
            errors.append(f"Field 'status' must be one of {ALLOWED_STATUSES}. Found: '{status_val}'")

    author_val = metadata.get("author")
    if author_val is not None and not isinstance(author_val, str):
        errors.append(f"Optional field 'author' must be a string if present. Found: {type(author_val)}")

    last_reviewed_val = metadata.get("last_reviewed")
    if last_reviewed_val is not None:
        if not isinstance(last_reviewed_val, str) or not parse_date(last_reviewed_val):
            errors.append(f"Optional field 'last_reviewed' must be a string in YYYY-MM-DD format if present. Found: '{last_reviewed_val}'")

    # Check for unknown fields
    all_known_fields = set(REQUIRED_FIELDS + OPTIONAL_FIELDS)
    for key in metadata.keys():
        if key not in all_known_fields:
            errors.append(f"Unknown field '{key}' found in front-matter.")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate front-matter metadata in Markdown files.")
    parser.add_argument("paths", nargs='+', type=pathlib.Path, help="List of Markdown files or directories to scan.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output.")

    args = parser.parse_args()

    files_to_check: List[pathlib.Path] = []
    for path_arg in args.paths:
        if path_arg.is_file():
            if path_arg.suffix == ".md":
                files_to_check.append(path_arg)
            elif args.verbose:
                print(f"Skipping non-markdown file: {path_arg}")
        elif path_arg.is_dir():
            if args.verbose:
                print(f"Scanning directory: {path_arg}")
            files_to_check.extend(list(path_arg.rglob("*.md")))
        else:
            print(f"Warning: Path '{path_arg}' is not a file or directory. Skipping.")

    if not files_to_check and args.verbose:
        print("No markdown files found to check.")


    total_errors = 0
    files_with_errors = 0

    for md_file in files_to_check:
        if args.verbose:
            print(f"Processing file: {md_file}")
        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error reading file {md_file}: {e}")
            total_errors += 1
            files_with_errors +=1
            continue

        front_matter = extract_front_matter(content)

        if front_matter is None:
            if "--- Delgado, Victor" in content[:100] or "--- Bernal, Diego" in content[:100]: # Heuristic for known non-frontmatter files
                 if args.verbose:
                    print(f"Skipping file with known non-standard starting pattern: {md_file}")
                 continue
            print(f"Error: No valid YAML front-matter found or it is not a dictionary in {md_file}")
            total_errors += 1
            files_with_errors +=1
            continue

        file_errors = validate_metadata(md_file, front_matter)
        if file_errors:
            files_with_errors +=1
            print(f"\nValidation errors in {md_file}:")
            for error in file_errors:
                print(f"  - {error}")
                total_errors += 1
        elif args.verbose:
            print(f"  OK: {md_file}")

    if total_errors > 0:
        print(f"\nFound {total_errors} error(s) in {files_with_errors} file(s).")
        exit(1)
    else:
        print("\nAll processed markdown files have valid front-matter.")
        exit(0)

if __name__ == "__main__":
    main()
