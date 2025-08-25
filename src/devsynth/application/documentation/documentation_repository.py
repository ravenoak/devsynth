"""
Documentation Repository module.

This module defines the DocumentationRepository class for storing and retrieving
documentation in a version-aware manner, integrating with the memory system.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.logging_setup import DevSynthLogger

# Create a logger for this module
logger = DevSynthLogger(__name__)


class DocumentationRepository:
    """
    Stores and retrieves documentation in a version-aware manner.

    This class integrates with the memory system to store documentation chunks
    in vector memory, metadata in structured memory, and relationships in the
    knowledge graph.
    """

    def __init__(
        self, memory_manager: MemoryManager, storage_path: Optional[str] = None
    ):
        """
        Initialize the documentation repository.

        Args:
            memory_manager: The memory manager to use for storage
            storage_path: Path to store documentation metadata (defaults to .devsynth/documentation)
        """
        self.memory_manager = memory_manager
        self.storage_path = storage_path or os.path.join(
            os.getcwd(), ".devsynth", "documentation"
        )
        self.metadata: Dict[str, Dict[str, Any]] = {}

        # Create the storage directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)

        # Load any existing metadata
        self._load_metadata()

        logger.info(
            f"Documentation repository initialized with storage path: {self.storage_path}"
        )

    def store_documentation(
        self, library: str, version: str, chunks: List[Dict[str, Any]]
    ) -> str:
        """
        Store documentation for a library version.

        Args:
            library: The name of the library
            version: The version of the library
            chunks: List of documentation chunks, each with 'content', 'title', and 'metadata'

        Returns:
            A unique ID for this documentation set
        """
        doc_id = f"{library}-{version}"

        # Store metadata
        self.metadata[doc_id] = {
            "library": library,
            "version": version,
            "chunk_count": len(chunks),
            "stored_at": datetime.now().isoformat(),
            "status": "active",
        }

        # Store each chunk in memory
        chunk_ids = []
        for i, chunk in enumerate(chunks):
            # Create a memory item for the chunk
            memory_item = MemoryItem(
                id=f"{doc_id}-chunk-{i}",
                content=chunk["content"],
                metadata={
                    "library": library,
                    "version": version,
                    "title": chunk.get("title", ""),
                    "source_url": chunk.get("metadata", {}).get("source_url", ""),
                    "section": chunk.get("metadata", {}).get("section", ""),
                    "type": "documentation",
                    "chunk_index": i,
                },
                memory_type=MemoryType.KNOWLEDGE_GRAPH,  # Using KNOWLEDGE_GRAPH since DOCUMENTATION is not in MemoryType
            )

            # Store in vector memory for semantic search
            self.memory_manager.store_memory_item(memory_item)

            # Store relationships in knowledge graph if available
            if self.memory_manager.has_graph_store():
                self._store_relationships(library, version, chunk)

            chunk_ids.append(memory_item.id)

        # Update metadata with chunk IDs
        self.metadata[doc_id]["chunk_ids"] = chunk_ids
        self._save_metadata()

        logger.info(
            f"Stored {len(chunks)} documentation chunks for {library} {version}"
        )
        return doc_id

    def get_documentation(self, library: str, version: str) -> Optional[Dict[str, Any]]:
        """
        Get documentation metadata for a library version.

        Args:
            library: The name of the library
            version: The version of the library

        Returns:
            Documentation metadata, or None if not found
        """
        doc_id = f"{library}-{version}"
        return self.metadata.get(doc_id)

    def has_documentation(self, library: str, version: str) -> bool:
        """
        Check if documentation exists for a library version.

        Args:
            library: The name of the library
            version: The version of the library

        Returns:
            True if documentation exists, False otherwise
        """
        doc_id = f"{library}-{version}"
        return doc_id in self.metadata

    def query_documentation(
        self,
        query: str,
        libraries: Optional[List[str]] = None,
        version_constraints: Optional[Dict[str, str]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Query documentation using semantic search.

        Args:
            query: The query string
            libraries: Optional list of libraries to search in
            version_constraints: Optional version constraints (e.g., {"numpy": ">= 1.20.0"})
            limit: Maximum number of results to return

        Returns:
            A list of documentation chunks matching the query
        """
        # Build metadata filter
        metadata_filter = {}
        if libraries:
            metadata_filter["library"] = {"$in": libraries}

        # Perform semantic search
        results = self.memory_manager.search_memory(
            query=query,
            memory_type="DOCUMENTATION",  # Using string instead of enum since DOCUMENTATION is not in MemoryType
            metadata_filter=metadata_filter,
            limit=limit * 2,  # Get more results than needed for filtering
        )

        # Filter by version constraints if provided
        if version_constraints:
            filtered_results = []
            for result in results:
                library = result.metadata.get("library")
                version = result.metadata.get("version")

                if library in version_constraints:
                    constraint = version_constraints[library]
                    if self._version_satisfies_constraint(version, constraint):
                        filtered_results.append(result)
                else:
                    filtered_results.append(result)

            results = filtered_results[:limit]
        else:
            results = results[:limit]

        # Convert to dictionaries
        return [
            {
                "id": result.id,
                "content": result.content,
                "library": result.metadata.get("library"),
                "version": result.metadata.get("version"),
                "title": result.metadata.get("title"),
                "source_url": result.metadata.get("source_url"),
                "section": result.metadata.get("section"),
                "relevance": result.score if hasattr(result, "score") else None,
            }
            for result in results
        ]

    def list_libraries(self) -> List[Dict[str, Any]]:
        """
        List all libraries with available documentation.

        Returns:
            A list of library metadata dictionaries
        """
        libraries = {}

        for doc_id, metadata in self.metadata.items():
            library = metadata["library"]
            version = metadata["version"]

            if library not in libraries:
                libraries[library] = {"name": library, "versions": []}

            libraries[library]["versions"].append(
                {
                    "version": version,
                    "stored_at": metadata["stored_at"],
                    "chunk_count": metadata["chunk_count"],
                }
            )

        return list(libraries.values())

    def mark_outdated(self, library: str, version: str) -> bool:
        """
        Mark documentation as outdated.

        Args:
            library: The name of the library
            version: The version of the library

        Returns:
            True if the documentation was marked as outdated, False if not found
        """
        doc_id = f"{library}-{version}"
        if doc_id not in self.metadata:
            return False

        self.metadata[doc_id]["status"] = "outdated"
        self.metadata[doc_id]["outdated_at"] = datetime.now().isoformat()
        self._save_metadata()

        logger.info(f"Marked documentation for {library} {version} as outdated")
        return True

    def delete_documentation(self, library: str, version: str) -> bool:
        """
        Delete documentation for a library version.

        Args:
            library: The name of the library
            version: The version of the library

        Returns:
            True if the documentation was deleted, False if not found
        """
        doc_id = f"{library}-{version}"
        if doc_id not in self.metadata:
            return False

        # Get chunk IDs
        chunk_ids = self.metadata[doc_id].get("chunk_ids", [])

        # Delete each chunk from memory
        for chunk_id in chunk_ids:
            self.memory_manager.delete_memory_item(chunk_id)

        # Delete metadata
        del self.metadata[doc_id]
        self._save_metadata()

        logger.info(f"Deleted documentation for {library} {version}")
        return True

    def _store_relationships(
        self, library: str, version: str, chunk: Dict[str, Any]
    ) -> None:
        """Store relationships in the knowledge graph."""
        # Extract entities and relationships from the chunk
        content = chunk["content"]
        title = chunk.get("title", "")
        metadata = chunk.get("metadata", {})

        # Add library-version relationship
        self.memory_manager.add_graph_triple(
            subject=f"library:{library}",
            predicate="hasVersion",
            object=f"version:{library}:{version}",
        )

        # Add document-library relationship
        doc_id = f"doc:{library}:{version}:{metadata.get('section', 'unknown')}"
        self.memory_manager.add_graph_triple(
            subject=doc_id, predicate="describesLibrary", object=f"library:{library}"
        )

        self.memory_manager.add_graph_triple(
            subject=doc_id,
            predicate="describesVersion",
            object=f"version:{library}:{version}",
        )

        # Extract and add function/class relationships if possible
        # This is a simple regex-based extraction and could be enhanced
        class_matches = re.findall(r"class\s+(\w+)", content)
        for class_name in class_matches:
            self.memory_manager.add_graph_triple(
                subject=f"class:{library}:{class_name}",
                predicate="definedIn",
                object=f"library:{library}",
            )

            self.memory_manager.add_graph_triple(
                subject=f"class:{library}:{class_name}",
                predicate="availableInVersion",
                object=f"version:{library}:{version}",
            )

        function_matches = re.findall(r"def\s+(\w+)", content)
        for function_name in function_matches:
            self.memory_manager.add_graph_triple(
                subject=f"function:{library}:{function_name}",
                predicate="definedIn",
                object=f"library:{library}",
            )

            self.memory_manager.add_graph_triple(
                subject=f"function:{library}:{function_name}",
                predicate="availableInVersion",
                object=f"version:{library}:{version}",
            )

    def _version_satisfies_constraint(self, version: str, constraint: str) -> bool:
        """Check if a version satisfies a constraint."""
        # Simple version comparison for common constraints
        # This could be enhanced with a proper version comparison library

        # Extract operator and version
        match = re.match(r"^\s*(>=|<=|>|<|==|!=)\s*(.+)\s*$", constraint)
        if not match:
            # If no operator, assume exact match
            return version == constraint

        operator, constraint_version = match.groups()

        # Convert versions to tuples of integers for comparison
        try:
            v1 = tuple(int(x) for x in version.split("."))
            v2 = tuple(int(x) for x in constraint_version.split("."))
        except ValueError:
            # If conversion fails, fall back to string comparison
            if operator == ">=":
                return version >= constraint_version
            elif operator == "<=":
                return version <= constraint_version
            elif operator == ">":
                return version > constraint_version
            elif operator == "<":
                return version < constraint_version
            elif operator == "==":
                return version == constraint_version
            elif operator == "!=":
                return version != constraint_version
            else:
                return False

        # Compare version tuples
        if operator == ">=":
            return v1 >= v2
        elif operator == "<=":
            return v1 <= v2
        elif operator == ">":
            return v1 > v2
        elif operator == "<":
            return v1 < v2
        elif operator == "==":
            return v1 == v2
        elif operator == "!=":
            return v1 != v2
        else:
            return False

    def _load_metadata(self) -> None:
        """Load documentation metadata from the storage path."""
        metadata_file = os.path.join(self.storage_path, "metadata.json")
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, "r") as f:
                    self.metadata = json.load(f)
                logger.debug("Loaded documentation metadata")
            except Exception as e:
                logger.error(f"Error loading documentation metadata: {str(e)}")
                self.metadata = {}
        else:
            self.metadata = {}

    def _save_metadata(self) -> None:
        """Save documentation metadata to the storage path."""
        metadata_file = os.path.join(self.storage_path, "metadata.json")
        try:
            with open(metadata_file, "w") as f:
                json.dump(self.metadata, f, indent=2)
            logger.debug("Saved documentation metadata")
        except Exception as e:
            logger.error(f"Error saving documentation metadata: {str(e)}")
