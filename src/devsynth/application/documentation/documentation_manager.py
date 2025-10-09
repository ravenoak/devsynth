"""
Documentation Manager module.

This module defines the DocumentationManager class for coordinating documentation
fetching, storage, and querying in a version-aware manner.
"""

import os
from typing import Any

from devsynth.application.documentation.documentation_fetcher import (
    DocumentationFetcher,
)
from devsynth.application.documentation.documentation_repository import (
    DocumentationRepository,
)
from devsynth.application.documentation.version_monitor import VersionMonitor
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.logging_setup import DevSynthLogger

# Create a logger for this module
logger = DevSynthLogger(__name__)


class DocumentationManager:
    """
    Coordinates documentation fetching, storage, and querying.

    This class provides a high-level interface for working with documentation,
    coordinating between the fetcher, repository, and version monitor.
    """

    def __init__(
        self,
        memory_manager: MemoryManager | None = None,
        storage_path: str | None = None,
    ):
        """
        Initialize the documentation manager.

        Args:
            memory_manager: Optional memory manager. If ``None`` a default
                :class:`~devsynth.application.memory.memory_manager.MemoryManager`
                will be created.
            storage_path: Path for documentation storage
                (default: .devsynth/documentation)
        """
        self.storage_path = storage_path or os.path.join(
            os.getcwd(), ".devsynth", "documentation"
        )

        if memory_manager is None:
            memory_manager = MemoryManager()

        # Create the storage directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)

        # Initialize components
        self.fetcher = DocumentationFetcher()
        self.repository = DocumentationRepository(memory_manager, self.storage_path)
        self.version_monitor = VersionMonitor(self.storage_path)

        logger.info(
            f"Documentation manager initialized with storage path: {self.storage_path}"
        )

    def fetch_documentation(
        self, library: str, version: str, force: bool = False, offline: bool = False
    ) -> dict[str, Any]:
        """
        Fetch documentation for a library version.

        Args:
            library: The name of the library
            version: The version of the library
            force: Whether to force a fresh fetch even if documentation exists

        Returns:
            A dictionary with information about the fetched documentation

        Raises:
            ValueError: If the library is unsupported or documentation
                cannot be fetched
        """
        # Check if documentation already exists
        if not force and self.repository.has_documentation(library, version):
            logger.info(f"Using cached documentation for {library} {version}")
            return {
                "library": library,
                "version": version,
                "source": "cache",
                "metadata": self.repository.get_documentation(library, version),
            }

        # If offline and no cached documentation is available raise an error
        if offline and not self.repository.has_documentation(library, version):
            raise ValueError(f"No cached documentation for {library} {version}")

        # Check if the library is supported
        if not self.fetcher.supports_library(library):
            raise ValueError(f"Library {library} is not supported")

        # Fetch documentation
        chunks = self.fetcher.fetch_documentation(library, version, offline=offline)
        if not chunks:
            raise ValueError(f"No documentation found for {library} {version}")

        # Store documentation
        doc_id = self.repository.store_documentation(library, version, chunks)

        # Register with version monitor
        self.version_monitor.register_library(library, version)

        return {
            "library": library,
            "version": version,
            "source": "fetched",
            "chunk_count": len(chunks),
            "doc_id": doc_id,
        }

    def query_documentation(
        self,
        query: str,
        libraries: list[str] | None = None,
        version_constraints: dict[str, str] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Query documentation using semantic search.

        Args:
            query: The query string
            libraries: Optional list of libraries to search in
            version_constraints: Optional version constraints
                (e.g., {"numpy": ">= 1.20.0"})
            limit: Maximum number of results to return

        Returns:
            A list of documentation chunks matching the query
        """
        return self.repository.query_documentation(
            query, libraries, version_constraints, limit
        )

    def list_libraries(self) -> list[dict[str, Any]]:
        """
        List all libraries with available documentation.

        Returns:
            A list of library metadata dictionaries
        """
        return self.repository.list_libraries()

    def check_for_updates(self) -> list[dict[str, Any]]:
        """
        Check for updates to documented libraries.

        Returns:
            A list of libraries with available updates
        """
        updates = []

        # Get all libraries
        libraries = self.repository.list_libraries()

        for library in libraries:
            library_name = library["name"]
            current_versions = [v["version"] for v in library["versions"]]

            # Check for new versions
            try:
                available_versions = self.fetcher.get_available_versions(library_name)
                new_versions = [
                    v for v in available_versions if v not in current_versions
                ]

                if new_versions:
                    # Find the latest version we have
                    latest_current = max(current_versions, key=self._version_key)

                    # Find newer versions
                    newer_versions = [
                        v
                        for v in new_versions
                        if self._version_key(v) > self._version_key(latest_current)
                    ]

                    if newer_versions:
                        # Mark current versions as outdated
                        for version in current_versions:
                            self.repository.mark_outdated(library_name, version)

                        updates.append(
                            {
                                "library": library_name,
                                "current_version": latest_current,
                                "available_versions": newer_versions,
                                "latest_available": max(
                                    newer_versions, key=self._version_key
                                ),
                            }
                        )
            except Exception as e:
                logger.warning(
                    f"Error checking for updates to {library_name}: {str(e)}"
                )

        return updates

    def update_documentation(
        self, library: str, from_version: str, to_version: str
    ) -> dict[str, Any]:
        """
        Update documentation from one version to another.

        Args:
            library: The name of the library
            from_version: The current version
            to_version: The new version

        Returns:
            A dictionary with information about the update

        Raises:
            ValueError: If the library is unsupported or documentation
                cannot be fetched
        """
        # Check if the current version exists
        if not self.repository.has_documentation(library, from_version):
            raise ValueError(f"No documentation found for {library} {from_version}")

        # Fetch the new version
        result = self.fetch_documentation(library, to_version, force=True)

        # Mark the old version as outdated
        self.repository.mark_outdated(library, from_version)

        return {
            "library": library,
            "from_version": from_version,
            "to_version": to_version,
            "status": "updated",
            "result": result,
        }

    def get_documentation_status(self, library: str, version: str) -> dict[str, Any]:
        """
        Get the status of documentation for a library version.

        Args:
            library: The name of the library
            version: The version of the library

        Returns:
            A dictionary with status information

        Raises:
            ValueError: If no documentation is found
        """
        metadata = self.repository.get_documentation(library, version)
        if not metadata:
            raise ValueError(f"No documentation found for {library} {version}")

        # Check if there are newer versions available
        try:
            available_versions = self.fetcher.get_available_versions(library)
            newer_versions = [
                v
                for v in available_versions
                if self._version_key(v) > self._version_key(version)
            ]

            return {
                "library": library,
                "version": version,
                "status": metadata.get("status", "active"),
                "stored_at": metadata.get("stored_at"),
                "chunk_count": metadata.get("chunk_count", 0),
                "has_newer_versions": len(newer_versions) > 0,
                "latest_available": (
                    max(available_versions, key=self._version_key)
                    if available_versions
                    else None
                ),
            }
        except Exception as e:
            logger.warning(f"Error checking for newer versions of {library}: {str(e)}")

            return {
                "library": library,
                "version": version,
                "status": metadata.get("status", "active"),
                "stored_at": metadata.get("stored_at"),
                "chunk_count": metadata.get("chunk_count", 0),
                "has_newer_versions": False,
                "latest_available": None,
                "error": str(e),
            }

    def get_function_documentation(self, function_name: str) -> list[dict[str, Any]]:
        """
        Get documentation for a specific function.

        Args:
            function_name: Fully qualified function name
                (e.g., "pandas.DataFrame.groupby")

        Returns:
            A list of documentation chunks for the function with
            additional metadata
        """
        # Extract the library name from the function name
        library = function_name.split(".")[0]

        # Query for function documentation
        query = f"function:{function_name}"
        results = self.query_documentation(query, libraries=[library])

        # Ensure results include parameter descriptions, return values, and examples
        for result in results:
            if "parameters" not in result:
                result["parameters"] = []
            if "returns" not in result:
                result["returns"] = ""
            if "examples" not in result:
                result["examples"] = []

        logger.info(
            f"Retrieved {len(results)} documentation chunks for function"
            f" {function_name}"
        )
        return results

    def get_class_documentation(self, class_name: str) -> list[dict[str, Any]]:
        """
        Get documentation for a specific class.

        Args:
            class_name: Fully qualified class name
                (e.g., "sklearn.ensemble.RandomForestClassifier")

        Returns:
            A list of documentation chunks for the class with
            additional metadata
        """
        # Extract the library name from the class name
        library = class_name.split(".")[0]

        # Query for class documentation
        query = f"class:{class_name}"
        results = self.query_documentation(query, libraries=[library])

        # Ensure results include constructor parameters, methods, and inheritance
        for result in results:
            if "constructor_params" not in result:
                result["constructor_params"] = []
            if "methods" not in result:
                result["methods"] = []
            if "inheritance" not in result:
                result["inheritance"] = []

        logger.info(
            f"Retrieved {len(results)} documentation chunks for class {class_name}"
        )
        return results

    def get_usage_examples(self, item_name: str) -> list[dict[str, Any]]:
        """
        Get usage examples for a specific function, class, or module.

        Args:
            item_name: The fully qualified name of the item (e.g., "numpy.array")

        Returns:
            A list of example code snippets with explanations
        """
        # Extract the library name from the item name
        library = item_name.split(".")[0]

        # Query for examples
        query = f"example:{item_name}"
        results = self.query_documentation(query, libraries=[library])

        # Process results to ensure they include code and explanations
        for result in results:
            if "code" not in result:
                result["code"] = ""
            if "explanation" not in result:
                result["explanation"] = ""

        # Sort by relevance (already done by query_documentation)
        logger.info(f"Retrieved {len(results)} examples for {item_name}")
        return results

    def get_api_compatibility(
        self, function_name: str, versions: list[str]
    ) -> dict[str, Any]:
        """
        Get compatibility information for a function across multiple versions.

        Args:
            function_name: The fully qualified name of the function
            versions: List of versions to compare

        Returns:
            A dictionary with compatibility information
        """
        # Extract the library name from the function name
        library = function_name.split(".")[0]

        # Get documentation for each version
        version_info = []
        for version in versions:
            try:
                doc = self.repository.get_documentation(library, version) or {}
                version_info.append(
                    {
                        "version": version,
                        "parameters": doc.get("parameters", []),
                        "changes": doc.get("changes", []),
                        "deprecated": doc.get("deprecated", []),
                    }
                )
            except Exception as e:
                logger.warning(
                    f"Error getting documentation for {library} {version}:" f" {str(e)}"
                )
                version_info.append({"version": version, "error": str(e)})

        # Sort by version
        version_info.sort(key=lambda v: self._version_key(v["version"]))

        logger.info(
            f"Retrieved compatibility information for {function_name}"
            f" across {len(versions)} versions"
        )
        return {"function": function_name, "versions": version_info}

    def get_related_functions(self, function_name: str) -> dict[str, Any]:
        """
        Get related functions for a specific function.

        Args:
            function_name: The fully qualified name of the function

        Returns:
            A dictionary with related function information
        """
        # Extract the library name from the function name
        library = function_name.split(".")[0]

        # Query for function documentation
        query = f"function:{function_name}"
        results = self.query_documentation(query, libraries=[library])

        related_functions = []
        if results:
            # Get related functions from the documentation
            related = results[0].get("related", [])
            version = (
                results[0].get("version") if isinstance(results[0], dict) else None
            )

            # Get documentation for each related function
            for rel_func in related:
                try:
                    doc_metadata = self.repository.get_documentation(
                        library,
                        version if isinstance(version, str) else "",
                        function=rel_func,
                    )
                    description = "No description available"
                    relationship = "Related function"
                    if isinstance(doc_metadata, dict):
                        description = doc_metadata.get("description", description)
                        relationship = doc_metadata.get("relationship", relationship)

                    related_functions.append(
                        {
                            "name": rel_func,
                            "description": description,
                            "relationship": relationship,
                        }
                    )
                except Exception as e:
                    logger.warning(
                        f"Error getting documentation for related function {rel_func}:"
                        f" {str(e)}"
                    )
                    related_functions.append(
                        {
                            "name": rel_func,
                            "description": "No description available",
                            "relationship": "Related function",
                            "error": str(e),
                        }
                    )

        logger.info(
            f"Retrieved {len(related_functions)} related functions for {function_name}"
        )
        return {"function": function_name, "related_functions": related_functions}

    def get_usage_patterns(self, function_name: str) -> dict[str, Any]:
        """
        Get common usage patterns for a specific function.

        Args:
            function_name: The fully qualified name of the function

        Returns:
            A dictionary with usage pattern information
        """
        # Extract the library name from the function name
        library = function_name.split(".")[0]

        # Query for function documentation
        query = f"function:{function_name}"
        results = self.query_documentation(query, libraries=[library])

        if not results:
            logger.warning(f"No documentation found for {function_name}")
            return {
                "function": function_name,
                "usage_patterns": [],
                "best_practices": [],
                "common_params": {},
            }

        # Extract usage patterns, best practices, and common parameters
        usage_patterns = results[0].get("usage_patterns", [])
        best_practices = results[0].get("best_practices", [])
        common_params = results[0].get("common_params", {})

        logger.info(
            f"Retrieved {len(usage_patterns)} usage patterns for {function_name}"
        )
        return {
            "function": function_name,
            "usage_patterns": usage_patterns,
            "best_practices": best_practices,
            "common_params": common_params,
        }

    def _version_key(self, version: str) -> tuple[int | str, ...]:
        """Convert a version string to a tuple for sorting."""
        # Convert each part to an integer if possible, otherwise use string
        parts: list[int | str] = []
        for part in version.split("."):
            try:
                parts.append(int(part))
            except ValueError:
                parts.append(part)
        return tuple(parts)
