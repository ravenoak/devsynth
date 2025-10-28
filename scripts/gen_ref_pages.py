"""Generate API reference pages for DevSynth.

This script generates a page for each module in the DevSynth package,
using the manifest.yaml file to understand project structure.
"""

import sys
from pathlib import Path

import mkdocs_gen_files
import yaml


def load_manifest(manifest_path):
    """Load the project manifest file."""
    try:
        with open(manifest_path) as f:
            return yaml.safe_load(f)
    except (FileNotFoundError, yaml.YAMLError) as e:
        print(f"Error loading manifest: {e}")
        return None


def main():
    root = Path(__file__).parent.parent
    manifest_path = root / "manifest.yaml"
    manifest = load_manifest(manifest_path)

    if not manifest:
        print("Warning: Using default src directory since manifest couldn't be loaded")
        src_dirs = [root / "src"]
    else:
        # Get source directories from project structure if available
        src_dirs = []
        if (
            "structure" in manifest
            and "directories" in manifest["structure"]
            and "source" in manifest["structure"]["directories"]
        ):
            for src_dir in manifest["structure"]["directories"]["source"]:
                src_dirs.append(root / src_dir)

        # Check for custom layouts and monorepos
        if "structure" in manifest and "customLayouts" in manifest["structure"]:
            custom = manifest["structure"]["customLayouts"]
            if (
                "type" in custom
                and custom["type"] == "monorepo"
                and "packages" in custom
            ):
                for package in custom["packages"]:
                    if "path" in package and "source" in package:
                        src_dirs.append(root / package["path"] / package["source"])

        # If no source directories specified, default to src/
        if not src_dirs:
            src_dirs = [root / "src"]

    nav = mkdocs_gen_files.Nav()

    # Process each source directory
    for src in src_dirs:
        if not src.exists():
            print(f"Warning: Source directory {src} does not exist")
            continue

        print(f"Generating API reference for {src}")
        for path in sorted(src.rglob("*.py")):
            module_path = path.relative_to(src).with_suffix("")
            doc_path = path.relative_to(src).with_suffix(".md")
            full_doc_path = Path("api_reference", doc_path)

            parts = tuple(module_path.parts)

            if parts[-1] == "__init__":
                parts = parts[:-1]
                doc_path = doc_path.with_name("index.md")
                full_doc_path = full_doc_path.with_name("index.md")
            elif parts[-1] == "__main__":
                continue

            nav[parts] = doc_path.as_posix()

            with mkdocs_gen_files.open(full_doc_path, "w") as fd:
                identifier = ".".join(parts)
                print("::: " + identifier, file=fd)

            mkdocs_gen_files.set_edit_path(full_doc_path, path.relative_to(root))

    with mkdocs_gen_files.open("api_reference/SUMMARY.md", "w") as nav_file:
        nav_file.writelines(nav.build_literate_nav())


if __name__ == "__main__":
    main()
