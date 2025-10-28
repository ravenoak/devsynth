"""
Project Model Module.

This module defines the domain model for representing a project's structure,
based on the manifest.yaml file and file system analysis.
"""

from __future__ import annotations

from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Set, Union

import networkx as nx

from devsynth.exceptions import ProjectModelError


class ArtifactType(Enum):
    """Types of artifacts that can be discovered in a project."""

    CODE = auto()
    TEST = auto()
    DOCUMENTATION = auto()
    CONFIGURATION = auto()
    BUILD = auto()
    RESOURCE = auto()
    UNKNOWN = auto()


class ProjectStructureType(Enum):
    """Types of project structures that can be defined in the manifest."""

    STANDARD = auto()  # Standard single project
    MONOREPO = auto()  # Monorepo with multiple projects/packages
    FEDERATED = auto()  # Federated repositories
    COMPOSITE = auto()  # Mixed structure with submodules
    CUSTOM = auto()  # Custom structure defined by user rules


class ArtifactProtocol(Protocol):
    """Protocol describing the minimum contract for project artifacts."""

    path: Path
    artifact_type: ArtifactType
    metadata: dict[str, Any]
    name: str
    is_directory: bool


class Artifact(ArtifactProtocol):
    """Represents a single artifact in the project (file, directory, etc.)."""

    def __init__(
        self,
        path: str | Path,
        artifact_type: ArtifactType = ArtifactType.UNKNOWN,
        metadata: dict[str, Any] | None = None,
    ):
        """
        Initialize an artifact.

        Args:
            path: Path to the artifact
            artifact_type: Type of the artifact
            metadata: Additional metadata about the artifact
        """
        self.path = Path(path)
        self.artifact_type = artifact_type
        self.metadata = metadata or {}
        self.name = self.path.name
        self.is_directory = self.path.is_dir() if self.path.exists() else False

    def __str__(self) -> str:
        return f"{self.name} ({self.artifact_type.name})"

    def __repr__(self) -> str:
        return f"Artifact(path='{self.path}', type={self.artifact_type.name}, metadata={self.metadata})"


class ProjectModel:
    """
    Represents the structure and components of a project.

    This class builds and maintains a model of the project's structure based on
    the manifest.yaml file and file system analysis. It provides methods for
    querying and navigating the project structure.
    """

    def __init__(self, project_root: str | Path, manifest_data: dict[str, Any]):
        """
        Initialize the project model.

        Args:
            project_root: Root directory of the project
            manifest_data: Data from the manifest.yaml file
        """
        self.project_root = Path(project_root).resolve()
        self.manifest_data = manifest_data
        self.artifacts: dict[str, Artifact] = {}
        self.structure_type = self._determine_structure_type()
        # Directed graph representing project structure where each node key is the
        # resolved artifact path and node data contains the ``artifact`` object.
        # The following contracts must always hold:
        # * ``self.graph`` and ``self.artifacts`` share identical node keys.
        # * Every edge's endpoints are valid artifact node keys.
        # * Edge attributes describe semantic relationships (currently
        #   ``relationship="contains"``) between artifacts.
        self.graph: nx.DiGraph[str] = nx.DiGraph()

    def _determine_structure_type(self) -> ProjectStructureType:
        """Determine the project structure type from the manifest data."""
        if (
            "structure" in self.manifest_data
            and "type" in self.manifest_data["structure"]
        ):
            structure_type = self.manifest_data["structure"]["type"].lower()
            if structure_type == "single_package":
                return ProjectStructureType.STANDARD
            elif structure_type == "monorepo":
                return ProjectStructureType.MONOREPO
            elif structure_type == "multi_project_submodules":
                return ProjectStructureType.FEDERATED
            elif structure_type == "custom":
                return ProjectStructureType.CUSTOM

        # Default to standard if not specified
        return ProjectStructureType.STANDARD

    def build_model(self) -> None:
        """
        Build the project model based on the manifest data and file system analysis.

        This method analyzes the project structure, identifies artifacts, and
        builds a graph representing the relationships between artifacts.
        """
        # Start with the project root
        root_artifact = Artifact(
            self.project_root, ArtifactType.UNKNOWN, {"is_root": True}
        )
        self.artifacts[str(self.project_root)] = root_artifact
        self.graph.add_node(str(self.project_root), artifact=root_artifact)

        # Process based on structure type
        if self.structure_type == ProjectStructureType.STANDARD:
            self._build_standard_model()
        elif self.structure_type == ProjectStructureType.MONOREPO:
            self._build_monorepo_model()
        elif self.structure_type == ProjectStructureType.FEDERATED:
            self._build_federated_model()
        elif self.structure_type == ProjectStructureType.CUSTOM:
            self._build_custom_model()

    def _build_standard_model(self) -> None:
        """Build a model for a standard single-package project."""
        # Get directories from manifest
        directories = self.manifest_data.get("structure", {}).get("directories", {})

        # Process source directories
        source_dirs = directories.get("source", [])
        for src_dir in source_dirs:
            src_path = self.project_root / src_dir
            if not src_path.exists():
                continue

            # Add source directory as an artifact
            src_artifact = Artifact(src_path, ArtifactType.CODE, {"role": "source"})
            self.artifacts[str(src_path)] = src_artifact
            self.graph.add_node(str(src_path), artifact=src_artifact)

            # Add edge from root to source directory
            self.graph.add_edge(
                str(self.project_root), str(src_path), relationship="contains"
            )

            # Process files in source directory
            self._process_directory(src_path, ArtifactType.CODE)

        # Process test directories
        test_dirs = directories.get("tests", [])
        for test_dir in test_dirs:
            test_path = self.project_root / test_dir
            if not test_path.exists():
                continue

            # Add test directory as an artifact
            test_artifact = Artifact(test_path, ArtifactType.TEST, {"role": "test"})
            self.artifacts[str(test_path)] = test_artifact
            self.graph.add_node(str(test_path), artifact=test_artifact)

            # Add edge from root to test directory
            self.graph.add_edge(
                str(self.project_root), str(test_path), relationship="contains"
            )

            # Process files in test directory
            self._process_directory(test_path, ArtifactType.TEST)

        # Process documentation directories
        doc_dirs = directories.get("docs", [])
        for doc_dir in doc_dirs:
            doc_path = self.project_root / doc_dir
            if not doc_path.exists():
                continue

            # Add documentation directory as an artifact
            doc_artifact = Artifact(
                doc_path, ArtifactType.DOCUMENTATION, {"role": "documentation"}
            )
            self.artifacts[str(doc_path)] = doc_artifact
            self.graph.add_node(str(doc_path), artifact=doc_artifact)

            # Add edge from root to documentation directory
            self.graph.add_edge(
                str(self.project_root), str(doc_path), relationship="contains"
            )

            # Process files in documentation directory
            self._process_directory(doc_path, ArtifactType.DOCUMENTATION)

    def _build_monorepo_model(self) -> None:
        """Build a model for a monorepo project with multiple packages."""
        # Get custom layouts from manifest
        custom_layouts = self.manifest_data.get("structure", {}).get(
            "customLayouts", {}
        )

        if not custom_layouts or custom_layouts.get("type") != "monorepo":
            # If no custom layouts or not a monorepo, fall back to standard model
            self._build_standard_model()
            return

        # Get packages root directory
        packages_root = custom_layouts.get("packagesRoot", "")
        packages_root_path = (
            self.project_root / packages_root if packages_root else self.project_root
        )

        # Add packages root as an artifact if it's not the project root
        if packages_root and packages_root_path != self.project_root:
            packages_root_artifact = Artifact(
                packages_root_path, ArtifactType.UNKNOWN, {"role": "packages_root"}
            )
            self.artifacts[str(packages_root_path)] = packages_root_artifact
            self.graph.add_node(
                str(packages_root_path), artifact=packages_root_artifact
            )
            self.graph.add_edge(
                str(self.project_root), str(packages_root_path), relationship="contains"
            )

        # Process each package
        packages = custom_layouts.get("packages", [])
        for package in packages:
            package_name = package.get("name", "")
            package_path = package.get("path", "")

            if not package_name or not package_path:
                continue

            # Get full path to package
            package_full_path = packages_root_path / package_path
            if not package_full_path.exists():
                continue

            # Add package as an artifact
            package_artifact = Artifact(
                package_full_path,
                ArtifactType.CODE,
                {"role": "package", "name": package_name},
            )
            self.artifacts[str(package_full_path)] = package_artifact
            self.graph.add_node(str(package_full_path), artifact=package_artifact)

            # Add edge from packages root to package
            if packages_root:
                self.graph.add_edge(
                    str(packages_root_path),
                    str(package_full_path),
                    relationship="contains",
                )
            else:
                self.graph.add_edge(
                    str(self.project_root),
                    str(package_full_path),
                    relationship="contains",
                )

            # Process source directory if specified
            source_dir = package.get("source", "")
            if source_dir:
                source_path = package_full_path / source_dir
                if source_path.exists():
                    source_artifact = Artifact(
                        source_path, ArtifactType.CODE, {"role": "source"}
                    )
                    self.artifacts[str(source_path)] = source_artifact
                    self.graph.add_node(str(source_path), artifact=source_artifact)
                    self.graph.add_edge(
                        str(package_full_path),
                        str(source_path),
                        relationship="contains",
                    )
                    self._process_directory(source_path, ArtifactType.CODE)

            # Process tests directory if specified
            tests_dir = package.get("tests", "")
            if tests_dir:
                tests_path = package_full_path / tests_dir
                if tests_path.exists():
                    tests_artifact = Artifact(
                        tests_path, ArtifactType.TEST, {"role": "test"}
                    )
                    self.artifacts[str(tests_path)] = tests_artifact
                    self.graph.add_node(str(tests_path), artifact=tests_artifact)
                    self.graph.add_edge(
                        str(package_full_path), str(tests_path), relationship="contains"
                    )
                    self._process_directory(tests_path, ArtifactType.TEST)

        # Process shared directories (outside of packages)
        self._process_shared_directories()

    def _process_shared_directories(self) -> None:
        """Process shared directories that are outside of package-specific directories."""
        # Get directories from manifest
        directories = self.manifest_data.get("structure", {}).get("directories", {})

        # Process shared documentation directories
        doc_dirs = directories.get("docs", [])
        for doc_dir in doc_dirs:
            doc_path = self.project_root / doc_dir
            if not doc_path.exists():
                continue

            # Skip if already processed as part of a package
            if str(doc_path) in self.artifacts:
                continue

            # Add documentation directory as an artifact
            doc_artifact = Artifact(
                doc_path, ArtifactType.DOCUMENTATION, {"role": "shared_documentation"}
            )
            self.artifacts[str(doc_path)] = doc_artifact
            self.graph.add_node(str(doc_path), artifact=doc_artifact)

            # Add edge from root to documentation directory
            self.graph.add_edge(
                str(self.project_root), str(doc_path), relationship="contains"
            )

            # Process files in documentation directory
            self._process_directory(doc_path, ArtifactType.DOCUMENTATION)

        # Process shared configuration directories
        # Look for common configuration directories and files
        config_paths = [
            self.project_root / ".github",
            self.project_root / "config",
            self.project_root / "configs",
            self.project_root / ".vscode",
            self.project_root / ".idea",
        ]

        # Common configuration files
        config_files = [
            ".gitignore",
            ".editorconfig",
            ".prettierrc",
            ".eslintrc",
            "tsconfig.json",
            "package.json",
            "pyproject.toml",
            "setup.py",
            "requirements.txt",
            "Dockerfile",
            "docker-compose.yml",
        ]

        # Process configuration directories
        for config_path in config_paths:
            if not config_path.exists() or str(config_path) in self.artifacts:
                continue

            # Add configuration directory as an artifact
            config_artifact = Artifact(
                config_path,
                ArtifactType.CONFIGURATION,
                {"role": "shared_configuration"},
            )
            self.artifacts[str(config_path)] = config_artifact
            self.graph.add_node(str(config_path), artifact=config_artifact)

            # Add edge from root to configuration directory
            self.graph.add_edge(
                str(self.project_root), str(config_path), relationship="contains"
            )

            # Process files in configuration directory
            self._process_directory(config_path, ArtifactType.CONFIGURATION)

        # Process configuration files
        for config_file in config_files:
            config_path = self.project_root / config_file
            if not config_path.exists() or str(config_path) in self.artifacts:
                continue

            # Add configuration file as an artifact
            config_artifact = Artifact(
                config_path,
                ArtifactType.CONFIGURATION,
                {"role": "shared_configuration"},
            )
            self.artifacts[str(config_path)] = config_artifact
            self.graph.add_node(str(config_path), artifact=config_artifact)

            # Add edge from root to configuration file
            self.graph.add_edge(
                str(self.project_root), str(config_path), relationship="contains"
            )

    def _build_federated_model(self) -> None:
        """Build a model for a federated project with multiple repositories."""
        # Get custom layouts from manifest
        custom_layouts = self.manifest_data.get("structure", {}).get(
            "customLayouts", {}
        )

        if not custom_layouts or custom_layouts.get("type") != "multi_project":
            # If no custom layouts or not a multi-project, fall back to standard model
            self._build_standard_model()
            return

        # Process each repository/submodule
        packages = custom_layouts.get("packages", [])
        for package in packages:
            package_name = package.get("name", "")
            package_path = package.get("path", "")

            if not package_name or not package_path:
                continue

            # Get full path to repository
            repo_path = self.project_root / package_path
            if not repo_path.exists():
                continue

            # Add repository as an artifact
            repo_artifact = Artifact(
                repo_path,
                ArtifactType.CODE,
                {"role": "repository", "name": package_name},
            )
            self.artifacts[str(repo_path)] = repo_artifact
            self.graph.add_node(str(repo_path), artifact=repo_artifact)

            # Add edge from project root to repository
            self.graph.add_edge(
                str(self.project_root), str(repo_path), relationship="contains"
            )

            # Process source directory if specified
            source_dir = package.get("source", "")
            if source_dir:
                source_path = repo_path / source_dir
                if source_path.exists():
                    source_artifact = Artifact(
                        source_path, ArtifactType.CODE, {"role": "source"}
                    )
                    self.artifacts[str(source_path)] = source_artifact
                    self.graph.add_node(str(source_path), artifact=source_artifact)
                    self.graph.add_edge(
                        str(repo_path), str(source_path), relationship="contains"
                    )
                    self._process_directory(source_path, ArtifactType.CODE)

            # Process tests directory if specified
            tests_dir = package.get("tests", "")
            if tests_dir:
                tests_path = repo_path / tests_dir
                if tests_path.exists():
                    tests_artifact = Artifact(
                        tests_path, ArtifactType.TEST, {"role": "test"}
                    )
                    self.artifacts[str(tests_path)] = tests_artifact
                    self.graph.add_node(str(tests_path), artifact=tests_artifact)
                    self.graph.add_edge(
                        str(repo_path), str(tests_path), relationship="contains"
                    )
                    self._process_directory(tests_path, ArtifactType.TEST)

        # Process shared directories (outside of repositories)
        self._process_shared_directories()

    def _build_custom_model(self) -> None:
        """Build a model for a custom project structure."""
        # For custom structures, we'll use a combination of:
        # 1. Explicit directories from the manifest
        # 2. Include/exclude patterns
        # 3. Entry points

        # Get structure information from manifest
        structure = self.manifest_data.get("structure", {})

        # Process explicit directories
        directories = structure.get("directories", {})

        # Process source directories
        source_dirs = directories.get("source", [])
        for src_dir in source_dirs:
            src_path = self.project_root / src_dir
            if not src_path.exists():
                continue

            # Add source directory as an artifact
            src_artifact = Artifact(src_path, ArtifactType.CODE, {"role": "source"})
            self.artifacts[str(src_path)] = src_artifact
            self.graph.add_node(str(src_path), artifact=src_artifact)

            # Add edge from root to source directory
            self.graph.add_edge(
                str(self.project_root), str(src_path), relationship="contains"
            )

            # Process files in source directory
            self._process_directory(src_path, ArtifactType.CODE)

        # Process test directories
        test_dirs = directories.get("tests", [])
        for test_dir in test_dirs:
            test_path = self.project_root / test_dir
            if not test_path.exists():
                continue

            # Add test directory as an artifact
            test_artifact = Artifact(test_path, ArtifactType.TEST, {"role": "test"})
            self.artifacts[str(test_path)] = test_artifact
            self.graph.add_node(str(test_path), artifact=test_artifact)

            # Add edge from root to test directory
            self.graph.add_edge(
                str(self.project_root), str(test_path), relationship="contains"
            )

            # Process files in test directory
            self._process_directory(test_path, ArtifactType.TEST)

        # Process documentation directories
        doc_dirs = directories.get("docs", [])
        for doc_dir in doc_dirs:
            doc_path = self.project_root / doc_dir
            if not doc_path.exists():
                continue

            # Add documentation directory as an artifact
            doc_artifact = Artifact(
                doc_path, ArtifactType.DOCUMENTATION, {"role": "documentation"}
            )
            self.artifacts[str(doc_path)] = doc_artifact
            self.graph.add_node(str(doc_path), artifact=doc_artifact)

            # Add edge from root to documentation directory
            self.graph.add_edge(
                str(self.project_root), str(doc_path), relationship="contains"
            )

            # Process files in documentation directory
            self._process_directory(doc_path, ArtifactType.DOCUMENTATION)

        # Process entry points
        entry_points = structure.get("entryPoints", [])
        for entry_point in entry_points:
            entry_path = self.project_root / entry_point
            if not entry_path.exists() or str(entry_path) in self.artifacts:
                continue

            # Add entry point as an artifact
            entry_artifact = Artifact(
                entry_path, ArtifactType.CODE, {"role": "entry_point"}
            )
            self.artifacts[str(entry_path)] = entry_artifact
            self.graph.add_node(str(entry_path), artifact=entry_artifact)

            # Add edge from root to entry point
            self.graph.add_edge(
                str(self.project_root), str(entry_path), relationship="contains"
            )

        # Process include patterns
        include_patterns = structure.get("include", [])
        for pattern in include_patterns:
            # Find files matching the pattern
            for item_path in self.project_root.glob(pattern):
                if (
                    not item_path.exists()
                    or item_path.is_dir()
                    or str(item_path) in self.artifacts
                ):
                    continue

                # Determine artifact type
                artifact_type = self._determine_artifact_type(
                    item_path, ArtifactType.UNKNOWN
                )

                # Add file as an artifact
                file_artifact = Artifact(
                    item_path,
                    artifact_type,
                    {
                        "extension": item_path.suffix,
                        "parent_dir": str(item_path.parent),
                        "included_by_pattern": pattern,
                    },
                )
                self.artifacts[str(item_path)] = file_artifact
                self.graph.add_node(str(item_path), artifact=file_artifact)

                # Add edge from parent directory to file
                parent_dir = str(item_path.parent)
                if parent_dir in self.artifacts:
                    self.graph.add_edge(
                        parent_dir, str(item_path), relationship="contains"
                    )
                else:
                    # If parent directory is not yet an artifact, add it
                    parent_artifact = Artifact(
                        item_path.parent, ArtifactType.UNKNOWN, {"role": "directory"}
                    )
                    self.artifacts[parent_dir] = parent_artifact
                    self.graph.add_node(parent_dir, artifact=parent_artifact)
                    self.graph.add_edge(
                        parent_dir, str(item_path), relationship="contains"
                    )

                    # Add edge from root to parent directory
                    if parent_dir != str(self.project_root):
                        self.graph.add_edge(
                            str(self.project_root), parent_dir, relationship="contains"
                        )

        # Process key artifacts if specified
        key_artifacts = self.manifest_data.get("keyArtifacts", {})
        key_docs = key_artifacts.get("docs", [])

        for key_doc in key_docs:
            doc_path = self.project_root / key_doc.get("path", "")
            if not doc_path.exists() or str(doc_path) in self.artifacts:
                continue

            # Add key document as an artifact
            doc_artifact = Artifact(
                doc_path,
                ArtifactType.DOCUMENTATION,
                {"role": "key_document", "purpose": key_doc.get("purpose", "")},
            )
            self.artifacts[str(doc_path)] = doc_artifact
            self.graph.add_node(str(doc_path), artifact=doc_artifact)

            # Add edge from root to key document
            self.graph.add_edge(
                str(self.project_root), str(doc_path), relationship="contains"
            )

    def get_artifact(self, path: str | Path) -> Artifact | None:
        """
        Get an artifact by path.

        Args:
            path: Path to the artifact

        Returns:
            The artifact if found, None otherwise
        """
        path_str = str(Path(path).resolve())
        return self.artifacts.get(path_str)

    def get_artifacts_by_type(self, artifact_type: ArtifactType) -> list[Artifact]:
        """
        Get all artifacts of a specific type.

        Args:
            artifact_type: Type of artifacts to retrieve

        Returns:
            List of artifacts of the specified type
        """
        return [a for a in self.artifacts.values() if a.artifact_type == artifact_type]

    def get_related_artifacts(self, artifact_path: str | Path) -> list[Artifact]:
        """
        Get artifacts related to the specified artifact.

        Args:
            artifact_path: Path to the artifact

        Returns:
            List of related artifacts

        Raises:
            ProjectModelError: If the artifact is not found
        """
        path_str = str(Path(artifact_path).resolve())
        if path_str not in self.artifacts:
            raise ProjectModelError(f"Artifact not found: {path_str}")

        related_paths: list[str] = []

        # Get successors (outgoing edges)
        if path_str in self.graph:
            related_paths.extend(self.graph.successors(path_str))

        # Get predecessors (incoming edges)
        related_paths.extend(self.graph.predecessors(path_str))

        return [self.artifacts[p] for p in related_paths if p in self.artifacts]

    def _process_directory(self, directory: Path, default_type: ArtifactType) -> None:
        """
        Process files in a directory and add them as artifacts to the model.

        Args:
            directory: Directory to process
            default_type: Default artifact type for files in this directory
        """
        if not directory.exists() or not directory.is_dir():
            return

        # Get ignore patterns from manifest
        ignore_patterns = self.manifest_data.get("structure", {}).get("ignore", [])

        # Process files and subdirectories
        for item_path in directory.glob("**/*"):
            # Skip directories, we're only interested in files
            if item_path.is_dir():
                continue

            # Check if the file should be ignored
            should_ignore = False
            for pattern in ignore_patterns:
                if item_path.match(pattern):
                    should_ignore = True
                    break

            if should_ignore:
                continue

            # Determine artifact type based on file extension
            artifact_type = self._determine_artifact_type(item_path, default_type)

            # Add file as an artifact
            file_artifact = Artifact(
                item_path,
                artifact_type,
                {"extension": item_path.suffix, "parent_dir": str(item_path.parent)},
            )
            self.artifacts[str(item_path)] = file_artifact
            self.graph.add_node(str(item_path), artifact=file_artifact)

            # Add edge from parent directory to file
            parent_dir = str(item_path.parent)
            if parent_dir in self.artifacts:
                self.graph.add_edge(parent_dir, str(item_path), relationship="contains")
            else:
                # If parent directory is not yet an artifact, add it
                parent_artifact = Artifact(
                    item_path.parent, default_type, {"role": "directory"}
                )
                self.artifacts[parent_dir] = parent_artifact
                self.graph.add_node(parent_dir, artifact=parent_artifact)
                self.graph.add_edge(parent_dir, str(item_path), relationship="contains")

                # Find the closest parent that is in the artifacts
                current_parent = item_path.parent
                while str(current_parent) != str(directory):
                    current_parent = current_parent.parent
                    if str(current_parent) in self.artifacts:
                        self.graph.add_edge(
                            str(current_parent), parent_dir, relationship="contains"
                        )
                        break

    def _determine_artifact_type(
        self, file_path: Path, default_type: ArtifactType
    ) -> ArtifactType:
        """
        Determine the artifact type based on the file extension and path.

        Args:
            file_path: Path to the file
            default_type: Default artifact type to use if no specific type is determined

        Returns:
            The determined artifact type
        """
        # First check if it's a test file based on name
        if "test" in file_path.name.lower() or "spec" in file_path.name.lower():
            return ArtifactType.TEST

        # Get file extension
        extension = file_path.suffix.lower()

        # Determine type based on extension
        if extension in [".py", ".js", ".ts", ".java", ".c", ".cpp", ".go", ".rs"]:
            return ArtifactType.CODE
        elif extension in [".md", ".rst", ".txt", ".pdf", ".html", ".docx"]:
            return ArtifactType.DOCUMENTATION
        elif extension in [".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf"]:
            return ArtifactType.CONFIGURATION
        elif extension in [
            ".sh",
            ".bat",
            ".ps1",
            ".cmd",
            ".Makefile",
            ".gradle",
            ".pom",
        ]:
            return ArtifactType.BUILD

        # If no specific type is determined, use the default
        return default_type

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the project model to a dictionary representation.

        Returns:
            Dictionary representation of the project model
        """
        return {
            "project_root": str(self.project_root),
            "structure_type": self.structure_type.name,
            "artifacts": {
                path: {
                    "name": artifact.name,
                    "type": artifact.artifact_type.name,
                    "is_directory": artifact.is_directory,
                    "metadata": artifact.metadata,
                }
                for path, artifact in self.artifacts.items()
            },
            "relationships": [
                {"source": source, "target": target, "metadata": data}
                for source, target, data in self.graph.edges(data=True)
            ],
        }
