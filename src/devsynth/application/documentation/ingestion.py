"""Documentation Ingestion Module

This module provides components for ingesting and processing
documentation from various sources.
"""

import hashlib
import json
import os
import re
from collections.abc import Callable, Iterable, Sequence
from datetime import datetime
from pathlib import Path
from typing import cast

import requests

from devsynth.application.documentation.models import (
    DocumentationManifest,
    Metadata,
    MetadataScalar,
)
from devsynth.exceptions import DevSynthError

from ...domain.models.memory import MemoryItem, MemoryType, MemoryVector
from ...logging_setup import DevSynthLogger
from ..memory.memory_manager import MemoryManager

logger = DevSynthLogger(__name__)


class DocumentationIngestionError(DevSynthError):
    """Error raised when documentation ingestion fails."""

    pass


class DocumentationIngestionManager:
    """
    Manager for ingesting and processing documentation from various sources.

    This class provides methods for ingesting documentation from files, directories,
    URLs, and other sources, processing it, and storing it in the memory system.
    """

    def __init__(self, memory_manager: MemoryManager | None = None):
        """
        Initialize the Documentation Ingestion Manager.

        Args:
            memory_manager: Optional memory manager to use for storing documentation
        """
        self.memory_manager: MemoryManager | None = memory_manager
        self.supported_file_types: dict[str, Callable[[str], str]] = {
            ".md": self._process_markdown,
            ".txt": self._process_text,
            ".json": self._process_json,
            ".py": self._process_python,
            ".html": self._process_html,
            ".rst": self._process_rst,
        }
        logger.info("Documentation Ingestion Manager initialized")

    def ingest_file(
        self,
        file_path: str | Path,
        metadata: Metadata | None = None,
    ) -> DocumentationManifest:
        """
        Ingest documentation from a file.

        Args:
            file_path: The path to the file to ingest
            metadata: Optional metadata to associate with the documentation

        Returns:
            A dictionary containing the ingested documentation

        Raises:
            DocumentationIngestionError: If the file cannot be read or processed
        """
        try:
            file_path = Path(file_path)

            # Check if the file exists
            if not file_path.exists():
                raise DocumentationIngestionError(f"File not found: {file_path}")

            # Check if the file type is supported
            file_ext = file_path.suffix.lower()
            if file_ext not in self.supported_file_types:
                raise DocumentationIngestionError(f"Unsupported file type: {file_ext}")

            # Read the file content
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Process the file based on its type
            processor = self.supported_file_types[file_ext]
            processed_content = processor(content)

            # Create metadata if not provided
            metadata = dict(metadata) if metadata else {}

            # Add file metadata
            metadata.update(
                {
                    "source": str(file_path),
                    "file_type": file_ext,
                    "file_name": file_path.name,
                    "ingestion_time": datetime.now().isoformat(),
                    "file_size": os.path.getsize(file_path),
                }
            )

            # Create the documentation item
            manifest = DocumentationManifest(
                content=processed_content,
                metadata=metadata,
            )

            if self.memory_manager:
                doc_id = self._store_in_memory(manifest)
                manifest = manifest.with_identifier(doc_id)

            logger.info(f"Ingested documentation from file: {file_path}")
            return manifest
        except Exception as e:
            logger.error(f"Failed to ingest documentation from file: {e}")
            raise DocumentationIngestionError(
                f"Failed to ingest documentation from file: {e}"
            )

    def ingest_directory(
        self,
        dir_path: str | Path,
        recursive: bool = True,
        file_types: Iterable[str] | None = None,
        metadata: Metadata | None = None,
    ) -> Sequence[DocumentationManifest]:
        """
        Ingest documentation from all supported files in a directory.

        Args:
            dir_path: The path to the directory to ingest
            recursive: Whether to recursively ingest files in subdirectories
            file_types: Optional iterable of file extensions to ingest
                (e.g., [".md", ".txt"])
            metadata: Optional metadata to associate with all documentation

        Returns:
            A sequence of dictionaries containing the ingested documentation

        Raises:
            DocumentationIngestionError: If the directory cannot be read
                or processed
        """
        try:
            dir_path = Path(dir_path)

            # Check if the directory exists
            if not dir_path.exists() or not dir_path.is_dir():
                raise DocumentationIngestionError(f"Directory not found: {dir_path}")

            # Filter file types if specified
            supported_types = set(self.supported_file_types.keys())
            if file_types is not None:
                supported_types = supported_types.intersection(set(file_types))

            # Find all supported files in the directory
            files = []
            if recursive:
                for root, _, filenames in os.walk(dir_path):
                    for filename in filenames:
                        file_path = Path(root) / filename
                        if file_path.suffix.lower() in supported_types:
                            files.append(file_path)
            else:
                for file_path in dir_path.iterdir():
                    if (
                        file_path.is_file()
                        and file_path.suffix.lower() in supported_types
                    ):
                        files.append(file_path)

            # Ingest each file
            results: list[DocumentationManifest] = []
            for file_path in files:
                try:
                    # Create file-specific metadata
                    file_metadata = dict(metadata) if metadata else {}
                    file_metadata["directory"] = str(dir_path)

                    # Ingest the file
                    doc_item = self.ingest_file(file_path, file_metadata)
                    results.append(doc_item)
                except Exception as e:
                    logger.warning(f"Failed to ingest file {file_path}: {e}")

            logger.info(
                f"Ingested {len(results)} documentation files from directory:"
                f" {dir_path}"
            )
            return tuple(results)
        except Exception as e:
            logger.error(f"Failed to ingest documentation from directory: {e}")
            raise DocumentationIngestionError(
                f"Failed to ingest documentation from directory: {e}"
            )

    def ingest_url(
        self, url: str, metadata: Metadata | None = None
    ) -> DocumentationManifest:
        """
        Ingest documentation from a URL.

        Args:
            url: The URL to ingest
            metadata: Optional metadata to associate with the documentation

        Returns:
            A dictionary containing the ingested documentation

        Raises:
            DocumentationIngestionError: If the URL cannot be accessed or processed
        """
        try:
            # Fetch the content from the URL
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            content = response.text

            # Determine the content type
            content_type = response.headers.get("Content-Type", "")

            # Process the content based on its type
            if "text/html" in content_type:
                processed_content = self._process_html(content)
            elif "text/markdown" in content_type or url.endswith(".md"):
                processed_content = self._process_markdown(content)
            elif "application/json" in content_type or url.endswith(".json"):
                processed_content = self._process_json(content)
            elif "text/x-rst" in content_type or url.endswith(".rst"):
                processed_content = self._process_rst(content)
            elif "text/plain" in content_type:
                processed_content = self._process_text(content)
            else:
                # Default to text processing
                processed_content = self._process_text(content)

            # Create metadata if not provided
            metadata = dict(metadata) if metadata else {}

            # Add URL metadata
            metadata.update(
                {
                    "source": url,
                    "content_type": content_type,
                    "ingestion_time": datetime.now().isoformat(),
                    "content_length": len(content),
                }
            )

            # Create the documentation item
            manifest = DocumentationManifest(
                content=processed_content,
                metadata=metadata,
            )

            if self.memory_manager:
                doc_id = self._store_in_memory(manifest)
                manifest = manifest.with_identifier(doc_id)

            logger.info(f"Ingested documentation from URL: {url}")
            return manifest
        except Exception as e:
            logger.error(f"Failed to ingest documentation from URL: {e}")
            raise DocumentationIngestionError(
                f"Failed to ingest documentation from URL: {e}"
            )

    def _process_markdown(self, content: str) -> str:
        """
        Process Markdown content.

        Args:
            content: The Markdown content to process

        Returns:
            The processed content
        """
        # Remove Markdown formatting for simplicity
        # Basic implementation; a more sophisticated one would use a
        # Markdown parser

        # Remove headers
        content = re.sub(r"#{1,6}\s+", "", content)

        # Remove emphasis
        content = re.sub(r"\*\*(.*?)\*\*", r"\1", content)  # Bold
        content = re.sub(r"\*(.*?)\*", r"\1", content)  # Italic
        content = re.sub(r"__(.*?)__", r"\1", content)  # Bold
        content = re.sub(r"_(.*?)_", r"\1", content)  # Italic

        # Remove links
        content = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", content)

        # Remove images
        content = re.sub(r"!\[(.*?)\]\(.*?\)", r"\1", content)

        # Remove code blocks
        content = re.sub(r"```.*?```", "", content, flags=re.DOTALL)

        # Remove inline code
        content = re.sub(r"`(.*?)`", r"\1", content)

        return content.strip()

    def _process_text(self, content: str) -> str:
        """
        Process plain text content.

        Args:
            content: The text content to process

        Returns:
            The processed content
        """
        # For plain text, just return the content as is
        return content.strip()

    def _process_json(self, content: str) -> str:
        """
        Process JSON content.

        Args:
            content: The JSON content to process

        Returns:
            The processed content
        """
        try:
            # Parse the JSON
            data = json.loads(content)

            # Convert to a formatted string
            formatted_content = json.dumps(data, indent=2)

            return formatted_content
        except json.JSONDecodeError:
            # If not valid JSON, treat as plain text
            return self._process_text(content)

    def _process_python(self, content: str) -> str:
        """
        Process Python content.

        Args:
            content: The Python content to process

        Returns:
            The processed content
        """
        # Extract docstrings and comments
        docstrings = re.findall(r'"""(.*?)"""', content, re.DOTALL)
        comments = re.findall(r"#\s*(.*?)$", content, re.MULTILINE)

        # Combine docstrings and comments
        extracted_text = "\n".join(docstrings) + "\n" + "\n".join(comments)

        # If no docstrings or comments, return the original content
        if not extracted_text.strip():
            return content

        return extracted_text.strip()

    def _process_html(self, content: str) -> str:
        """
        Process HTML content.

        Args:
            content: The HTML content to process

        Returns:
            The processed content
        """
        # Remove HTML tags for simplicity
        # Basic implementation; a full HTML parser would be better
        content = re.sub(r"<[^>]*>", "", content)

        # Remove extra whitespace
        content = re.sub(r"\s+", " ", content)

        return content.strip()

    def _process_rst(self, content: str) -> str:
        """
        Process reStructuredText content.

        Args:
            content: The reStructuredText content to process

        Returns:
            The processed content
        """
        # Remove RST formatting for simplicity
        # Basic implementation; a full RST parser would be better

        # Remove section headers
        content = re.sub(r'[=\-`:\'"~^_*+#<>]{3,}\n', "", content)

        # Remove directives
        content = re.sub(r"\.\. \w+::\s*\n(?:\s+.*\n)*", "", content)

        # Remove roles
        content = re.sub(r":\w+:`(.*?)`", r"\1", content)

        return content.strip()

    def _store_in_memory(self, manifest: DocumentationManifest) -> str:
        """
        Store documentation in memory.

        Args:
            content: The documentation content to store
            metadata: The metadata to associate with the documentation

        Returns:
            The ID of the stored documentation
        """
        if not self.memory_manager:
            raise DocumentationIngestionError(
                "No memory manager provided for storing documentation"
            )
        assert self.memory_manager is not None

        # Create a unique ID based on content and source
        metadata = dict(manifest.metadata)
        source = metadata.get("source", "unknown")
        content = manifest.content
        # Use SHA-256 for a more secure and collision-resistant hash
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        doc_id = f"doc_{source}_{content_hash}"

        # Record the documentation type in metadata for easier querying.
        metadata.setdefault("type", MemoryType.DOCUMENTATION.value)

        # Create a memory item using the DOCUMENTATION memory type.
        memory_item = MemoryItem(
            id=doc_id,
            content=manifest.content,
            memory_type=MemoryType.DOCUMENTATION,
            metadata=metadata,
        )

        # Store the memory item
        stored_id = cast(str, self.memory_manager.store(memory_item))

        logger.info(f"Stored documentation in memory with ID: {stored_id}")
        return stored_id

    def search_documentation(
        self,
        query: str,
        limit: int = 10,
        metadata_filter: dict[str, MetadataScalar] | None = None,
    ) -> Sequence[MemoryVector | MemoryItem]:
        """Search ingested documentation using the memory manager."""

        if not self.memory_manager:
            raise DocumentationIngestionError(
                "No memory manager provided for searching documentation"
            )
        assert self.memory_manager is not None

        vector_results: Sequence[MemoryVector] = self.memory_manager.search_memory(
            query=query,
            memory_type=MemoryType.DOCUMENTATION,
            metadata_filter=metadata_filter or {},
            limit=limit,
        )

        if vector_results:
            return tuple(vector_results)

        # Fallback to simple metadata search if no vector adapter results
        query_filter: dict[str, MetadataScalar] = {
            "type": MemoryType.DOCUMENTATION.value
        }
        if metadata_filter:
            query_filter.update(metadata_filter)
        item_results: Sequence[MemoryItem] = self.memory_manager.query_by_metadata(
            query_filter
        )

        return tuple(item_results)

    def semantic_search(
        self, query: str, limit: int = 10
    ) -> Sequence[MemoryVector | MemoryItem]:
        """Alias for :meth:`search_documentation` for compatibility."""

        return self.search_documentation(query, limit=limit)

    def ingest_from_project_config(
        self,
        project_root: str | Path | None = None,
        manifest_path: str | Path | None = None,
        docs_dirs: Iterable[str] | None = None,
        non_interactive: bool = False,
    ) -> Sequence[DocumentationManifest]:
        """Ingest documentation based on ``.devsynth/project.yaml``.

        Args:
            project_root: Root directory of the project. Defaults to the current
                working directory.
            manifest_path: Optional path to a manifest file. When provided the
                project configuration is loaded relative to this file.
            docs_dirs: Optional iterable of documentation directories to ingest.
                If not supplied, uses the ``docs`` directories defined in the
                project configuration or ``["docs"]`` as a fallback.
            non_interactive: When ``True`` disables interactive prompts for
                automation and sets the ``DEVSYNTH_NONINTERACTIVE`` environment
                variable.
        """

        from devsynth.config import load_project_config

        if non_interactive:
            os.environ["DEVSYNTH_NONINTERACTIVE"] = "1"

        root = Path(project_root or os.getcwd())

        if manifest_path:
            config = load_project_config(Path(manifest_path).parent)
        else:
            config = load_project_config(root)

        docs_dirs = tuple(docs_dirs or config.config.directories.get("docs", ["docs"]))
        results: list[DocumentationManifest] = []

        for rel in docs_dirs:
            doc_dir = root / rel
            if doc_dir.exists():
                results.extend(self.ingest_directory(doc_dir))

        return tuple(results)
