import json
import jsonschema
import yaml
from pathlib import Path
import sys
import datetime

def validate_manifest(manifest_path: Path, schema_path: Path, project_root_dir: Path) -> bool:
    """Validates the manifest file against the JSON schema and performs additional checks.

    Args:
        manifest_path: Path to the manifest.yaml file
        schema_path: Path to the manifest_schema.json file
        project_root_dir: Root directory of the project

    Returns:
        True if validation passes, False otherwise
    """
    try:
        schema = json.loads(schema_path.read_text(encoding='utf-8'))

        # Load manifest
        if not manifest_path.exists():
            print(f"Error: Manifest file not found at {manifest_path}")
            return False

        try:
            manifest = yaml.safe_load(manifest_path.read_text(encoding='utf-8'))
        except yaml.YAMLError as e:
            print(f"Error: Failed to parse manifest YAML: {e}")
            return False

        # Validate against schema
        try:
            jsonschema.validate(instance=manifest, schema=schema)
        except jsonschema.exceptions.ValidationError as e:
            print(f"Error: Manifest fails schema validation: {e}")
            return False

        print("✅ Manifest passes JSON schema validation")

        # Additional validations
        validation_results = []
        validation_results.append(validate_paths_exist(manifest, project_root_dir))
        validation_results.append(validate_dates(manifest))
        validation_results.append(validate_version_format(manifest))
        validation_results.append(validate_project_structure(manifest, project_root_dir))

        if all(validation_results):
            print("✅ All validation checks passed")
            return True
        else:
            print("❌ One or more validation checks failed")
            return False

    except Exception as e:
        print(f"Error during validation: {e}")
        return False


def validate_paths_exist(manifest: dict, project_root: Path) -> bool:
    """Validates that file paths referenced in the manifest exist in the project."""
    all_valid = True

    # Check source directories
    if 'structure' in manifest and 'directories' in manifest['structure']:
        dirs = manifest['structure']['directories']
        for dir_type in ['source', 'tests', 'docs']:
            if dir_type in dirs:
                for dir_path in dirs[dir_type]:
                    full_path = project_root / dir_path
                    if not full_path.exists() or not full_path.is_dir():
                        print(f"Error: {dir_type} directory does not exist: {dir_path}")
                        all_valid = False

    # Check custom layouts for monorepos
    if 'structure' in manifest and 'customLayouts' in manifest['structure']:
        custom = manifest['structure']['customLayouts']
        if 'type' in custom and custom['type'] == 'monorepo' and 'packages' in custom:
            for package in custom['packages']:
                if 'path' in package:
                    pkg_path = project_root / package['path']
                    if not pkg_path.exists() or not pkg_path.is_dir():
                        print(f"Error: Package path does not exist: {package['path']}")
                        all_valid = False

                    # Check source/tests within package
                    for dir_type in ['source', 'tests']:
                        if dir_type in package:
                            dir_path = pkg_path / package[dir_type]
                            if not dir_path.exists() or not dir_path.is_dir():
                                print(f"Error: Package {dir_type} directory does not exist: {package['path']}/{package[dir_type]}")
                                all_valid = False

    # Check entry points
    if 'structure' in manifest and 'entryPoints' in manifest['structure']:
        for entry_point in manifest['structure']['entryPoints']:
            full_path = project_root / entry_point
            if not full_path.exists() or not full_path.is_file():
                print(f"Error: Entry point does not exist: {entry_point}")
                all_valid = False

    # Check key artifacts
    if 'keyArtifacts' in manifest and 'docs' in manifest['keyArtifacts']:
        for doc in manifest['keyArtifacts']['docs']:
            if 'path' in doc:
                doc_path = project_root / doc['path']
                if not doc_path.exists():
                    print(f"Error: Document path does not exist: {doc['path']}")
                    all_valid = False

    if all_valid:
        print("✅ All referenced paths exist")

    return all_valid


def validate_dates(manifest: dict) -> bool:
    """Validates that dates in the manifest are in ISO format (YYYY-MM-DD)."""
    all_valid = True

    # Check version history dates
    if 'metadata' in manifest and 'versionHistory' in manifest['metadata']:
        for version in manifest['metadata']['versionHistory']:
            if 'date' in version:
                try:
                    datetime.datetime.fromisoformat(version['date'])
                except ValueError:
                    print(f"Error: Invalid date format in version history: {version['date']}. Use ISO format (YYYY-MM-DD).")
                    all_valid = False

    # Check last updated date
    if 'metadata' in manifest and 'lastUpdated' in manifest['metadata']:
        try:
            datetime.datetime.fromisoformat(manifest['metadata']['lastUpdated'])
        except ValueError:
            print(f"Error: Invalid lastUpdated date format: {manifest['metadata']['lastUpdated']}. Use ISO format (YYYY-MM-DD).")
            all_valid = False

    if all_valid:
        print("✅ Date format validation passed")

    return all_valid


def validate_version_format(manifest: dict) -> bool:
    """Validates that version strings follow semantic versioning (major.minor.patch)."""
    import re
    semver_pattern = re.compile(r'^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$')
    all_valid = True

    # Check current version
    if 'metadata' in manifest and 'version' in manifest['metadata']:
        version = manifest['metadata']['version']
        if not semver_pattern.match(version):
            print(f"Error: Invalid version format: {version}. Use semantic versioning (e.g., 1.0.0).")
            all_valid = False

    # Check version history
    if 'metadata' in manifest and 'versionHistory' in manifest['metadata']:
        for version_entry in manifest['metadata']['versionHistory']:
            if 'version' in version_entry:
                version = version_entry['version']
                if not semver_pattern.match(version):
                    print(f"Error: Invalid version format in history: {version}. Use semantic versioning (e.g., 1.0.0).")
                    all_valid = False

    if all_valid:
        print("✅ Version format validation passed")

    return all_valid


def validate_project_structure(manifest: dict, project_root: Path) -> bool:
    """
    Validates that the project structure defined in the manifest matches the actual project structure.

    This checks the structure section which defines the project type (single_package, monorepo, etc.)
    and validates that the corresponding directories and files exist as expected.

    Args:
        manifest: The loaded manifest dictionary
        project_root: Root directory of the project

    Returns:
        True if the project structure is valid, False otherwise
    """
    all_valid = True

    # Skip if structure is not defined
    if 'structure' not in manifest:
        print("⚠️ No structure defined in manifest, skipping structure validation")
        return True

    project_structure = manifest['structure']
    project_type = project_structure.get('type', 'single_package')

    # Validate single package structure
    if project_type == 'single_package':
        # Check source directories
        if 'directories' in project_structure and 'source' in project_structure['directories']:
            for source_dir in project_structure['directories']['source']:
                source_path = project_root / source_dir
                if not source_path.exists() or not source_path.is_dir():
                    print(f"Error: Source directory does not exist: {source_dir}")
                    all_valid = False

                # Check for Python package structure if primaryLanguage is Python
                if project_structure.get('primaryLanguage', '').lower() == 'python':
                    # Look for __init__.py in source directories
                    init_files = list(source_path.glob('**/__init__.py'))
                    if not init_files:
                        print(f"Warning: No __init__.py files found in source directory: {source_dir}")

        # Check test directories
        if 'directories' in project_structure and 'tests' in project_structure['directories']:
            for test_dir in project_structure['directories']['tests']:
                test_path = project_root / test_dir
                if not test_path.exists() or not test_path.is_dir():
                    print(f"Error: Test directory does not exist: {test_dir}")
                    all_valid = False

        # Check docs directories
        if 'directories' in project_structure and 'docs' in project_structure['directories']:
            for docs_dir in project_structure['directories']['docs']:
                docs_path = project_root / docs_dir
                if not docs_path.exists() or not docs_path.is_dir():
                    print(f"Error: Docs directory does not exist: {docs_dir}")
                    all_valid = False

    # Validate monorepo structure
    elif project_type == 'monorepo':
        # Check customLayouts for monorepo configuration
        if 'customLayouts' in project_structure:
            custom = project_structure['customLayouts']
            if 'type' in custom and custom['type'] == 'monorepo' and 'packages' in custom:
                for package in custom['packages']:
                    if 'path' in package:
                        pkg_path = project_root / package['path']
                        if not pkg_path.exists() or not pkg_path.is_dir():
                            print(f"Error: Package path does not exist: {package['path']}")
                            all_valid = False

                        # Check source/tests within package
                        for dir_type in ['source', 'tests']:
                            if dir_type in package:
                                dir_path = pkg_path / package[dir_type]
                                if not dir_path.exists() or not dir_path.is_dir():
                                    print(f"Error: Package {dir_type} directory does not exist: {package['path']}/{package[dir_type]}")
                                    all_valid = False
            else:
                print("Warning: Monorepo type specified but customLayouts is missing or incomplete")
        else:
            print("Warning: Monorepo type specified but customLayouts is not defined")

    # Validate multi-project submodules structure
    elif project_type == 'multi_project_submodules':
        # Check customLayouts for multi-project configuration
        if 'customLayouts' in project_structure:
            custom = project_structure['customLayouts']
            if 'type' in custom and custom['type'] == 'multi_project' and 'packages' in custom:
                for package in custom['packages']:
                    if 'path' in package:
                        pkg_path = project_root / package['path']
                        if not pkg_path.exists() or not pkg_path.is_dir():
                            print(f"Error: Submodule path does not exist: {package['path']}")
                            all_valid = False
            else:
                print("Warning: Multi-project type specified but customLayouts is missing or incomplete")
        else:
            print("Warning: Multi-project type specified but customLayouts is not defined")

    # Validate custom structure
    elif project_type == 'custom':
        # For custom type, we just check the basic directories
        if 'directories' in project_structure:
            dirs = project_structure['directories']
            for dir_type in ['source', 'tests', 'docs']:
                if dir_type in dirs:
                    for dir_path in dirs[dir_type]:
                        full_path = project_root / dir_path
                        if not full_path.exists() or not full_path.is_dir():
                            print(f"Error: {dir_type} directory does not exist: {dir_path}")
                            all_valid = False
        else:
            print("Warning: Custom type specified but directories are not defined")

    # Unknown project type
    else:
        print(f"Warning: Unknown project structure type: {project_type}. Expected one of: single_package, monorepo, multi_project_submodules, custom")

    if all_valid:
        print(f"✅ Project structure validation passed for type: {project_type}")

    return all_valid


if __name__ == "__main__":
    # Get project root directory (parent of scripts directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    manifest_path = project_root / "manifest.yaml"
    schema_path = project_root / "docs" / "manifest_schema.json"

    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Validate DevSynth manifest.yaml against schema and project structure")
    parser.add_argument("--manifest", help="Path to manifest.yaml file", default=manifest_path)
    parser.add_argument("--schema", help="Path to manifest_schema.json file", default=schema_path)
    parser.add_argument("--project-root", help="Project root directory", default=project_root)
    parser.add_argument("--verbose", "-v", action="store_true", help="Show verbose output")
    args = parser.parse_args()

    # Convert to Path objects
    manifest_path = Path(args.manifest)
    schema_path = Path(args.schema)
    project_root = Path(args.project_root)

    # Print information if verbose
    if args.verbose:
        print(f"Validating manifest: {manifest_path}")
        print(f"Using schema: {schema_path}")
        print(f"Project root: {project_root}")

    # Run validation
    success = validate_manifest(manifest_path, schema_path, project_root)

    # Exit with appropriate status code
    sys.exit(0 if success else 1)
