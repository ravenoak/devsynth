"""
Documentation Fetcher module.

This module defines the DocumentationFetcher class for fetching documentation
from various sources, including official documentation sites, PyPI, and GitHub.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping

import requests

from devsynth.application.documentation.models import (
    DocumentationChunk,
    DownloadManifest,
    Metadata,
)
from devsynth.logging_setup import DevSynthLogger

# Create a logger for this module
logger = DevSynthLogger(__name__)


class DocumentationSource(ABC):
    """Abstract base class for documentation sources."""

    def __init__(self, downloader: Callable[[str], DownloadManifest]) -> None:
        self._downloader = downloader

    @abstractmethod
    def fetch_documentation(
        self, library: str, version: str, offline: bool = False
    ) -> list[DocumentationChunk]:
        """
        Fetch documentation for a library version.

        Args:
            library: The name of the library
            version: The version of the library

        Returns:
            A list of documentation chunks
        """
        raise NotImplementedError(
            "fetch_documentation must be implemented by subclasses"
        )

    @abstractmethod
    def supports_library(self, library: str) -> bool:
        """
        Check if this source supports a library.

        Args:
            library: The name of the library

        Returns:
            True if the library is supported, False otherwise
        """
        raise NotImplementedError("supports_library must be implemented by subclasses")

    @abstractmethod
    def get_available_versions(self, library: str) -> list[str]:
        """
        Get available versions for a library.

        Args:
            library: The name of the library

        Returns:
            A list of available versions
        """
        raise NotImplementedError(
            "get_available_versions must be implemented by subclasses"
        )


class PyPIDocumentationSource(DocumentationSource):
    """Fetches documentation from PyPI and ReadTheDocs."""

    def __init__(self, downloader: Callable[[str], DownloadManifest]) -> None:
        """Initialize the PyPI documentation source."""
        super().__init__(downloader)
        self.cache_dir = os.path.join(tempfile.gettempdir(), "devsynth_docs_cache")
        os.makedirs(self.cache_dir, exist_ok=True)

    def fetch_documentation(
        self, library: str, version: str, offline: bool = False
    ) -> list[DocumentationChunk]:
        """Fetch documentation for a Python library."""
        logger.info(
            "Fetching documentation for %s %s from PyPI/ReadTheDocs",
            library,
            version,
        )

        # Try to get documentation from ReadTheDocs first
        chunks = self._fetch_from_readthedocs(library, version)
        if chunks:
            return chunks

        # Fall back to PyPI documentation
        chunks = self._fetch_from_pypi(library, version)
        if chunks:
            return chunks

        if offline:
            return []

        # If all else fails, try to extract docstrings from the package
        return self._extract_docstrings(library, version)

    def supports_library(self, library: str) -> bool:
        """Check if this source supports a library."""
        try:
            manifest = self._downloader(f"https://pypi.org/pypi/{library}/json")
            return bool(manifest)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Error checking PyPI for %s: %s", library, exc)
            return False

    def get_available_versions(self, library: str) -> list[str]:
        """Get available versions for a library from PyPI."""
        try:
            manifest = self._downloader(f"https://pypi.org/pypi/{library}/json")
            if not manifest:
                return []
            data = json.loads(manifest.content)
            releases = data.get("releases", {})
            if isinstance(releases, Mapping):
                return list(releases.keys())
            return []
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning(
                "Error getting versions for %s from PyPI: %s",
                library,
                exc,
            )
            return []

    def _fetch_from_readthedocs(
        self, library: str, version: str
    ) -> list[DocumentationChunk]:
        """Fetch documentation from ReadTheDocs."""
        urls = [
            f"https://{library}.readthedocs.io/en/{version}/",
            f"https://{library}.readthedocs.io/en/v{version}/",
            f"https://readthedocs.org/projects/{library}/versions/{version}/",
        ]

        for url in urls:
            manifest = self._downloader(url)
            if manifest:
                return self._parse_html_documentation(
                    manifest.content, url, library, version
                )
            if manifest.error:
                logger.debug(
                    "Error fetching from ReadTheDocs URL %s: %s",
                    url,
                    manifest.error,
                )
        return []

    def _fetch_from_pypi(self, library: str, version: str) -> list[DocumentationChunk]:
        """Fetch documentation from PyPI."""
        try:
            manifest = self._downloader(
                f"https://pypi.org/pypi/{library}/{version}/json"
            )
            if not manifest:
                return []

            data = json.loads(manifest.content)
            project_urls = data.get("info", {}).get("project_urls", {})
            if isinstance(project_urls, Mapping):
                doc_url = project_urls.get("Documentation")
            else:
                doc_url = None

            if isinstance(doc_url, str):
                doc_manifest = self._downloader(doc_url)
                if doc_manifest:
                    return self._parse_html_documentation(
                        doc_manifest.content, doc_url, library, version
                    )
                if doc_manifest.error:
                    logger.debug(
                        "Error fetching from documentation URL %s: %s",
                        doc_url,
                        doc_manifest.error,
                    )

            description = data.get("info", {}).get("description", "")
            if isinstance(description, str) and description:
                return self._parse_markdown_documentation(description, library, version)

            return []
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning(
                "Error fetching from PyPI for %s %s: %s",
                library,
                version,
                exc,
            )
            return []

    def _extract_docstrings(
        self, library: str, version: str
    ) -> list[DocumentationChunk]:
        """Extract docstrings from a Python package."""
        logger.info("Attempting to extract docstrings from %s %s", library, version)

        venv_dir = os.path.join(self.cache_dir, f"{library}_{version}_venv")
        script_path = os.path.join(
            self.cache_dir, f"extract_docstrings_{library}_{version}.py"
        )

        if os.path.exists(venv_dir):
            shutil.rmtree(venv_dir)

        try:
            subprocess.run(["python", "-m", "venv", venv_dir], check=True)

            pip_path = (
                os.path.join(venv_dir, "bin", "pip")
                if os.name != "nt"
                else os.path.join(venv_dir, "Scripts", "pip.exe")
            )
            subprocess.run([pip_path, "install", f"{library}=={version}"], check=True)

            python_path = (
                os.path.join(venv_dir, "bin", "python")
                if os.name != "nt"
                else os.path.join(venv_dir, "Scripts", "python.exe")
            )

            with open(script_path, "w", encoding="utf-8") as script_file:
                script_file.write(self._get_docstring_extraction_script(library))

            result = subprocess.run(
                [python_path, script_path], capture_output=True, text=True, check=False
            )

            if result.returncode == 0 and result.stdout:
                try:
                    docstrings = json.loads(result.stdout)
                    return self._convert_docstrings_to_chunks(
                        docstrings, library, version
                    )
                except json.JSONDecodeError:
                    logger.error(
                        "Error parsing docstring output for %s %s", library, version
                    )

            return []
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error(
                "Error extracting docstrings for %s %s: %s", library, version, exc
            )
            return []
        finally:
            if os.path.exists(venv_dir):
                shutil.rmtree(venv_dir)
            if os.path.exists(script_path):
                os.remove(script_path)

    def _parse_html_documentation(
        self, html: str, base_url: str, library: str, version: str
    ) -> list[DocumentationChunk]:
        """Parse HTML documentation into chunks."""
        chunks: list[DocumentationChunk] = []
        sections = re.split(r"<h[1-3][^>]*>(.*?)</h[1-3]>", html)

        current_title = ""
        current_content = ""

        for index, section in enumerate(sections):
            if index % 2 == 0:
                if current_title:
                    content = re.sub(r"<[^>]+>", " ", section)
                    content = re.sub(r"\s+", " ", content).strip()

                    if content:
                        chunks.append(
                            DocumentationChunk(
                                title=current_title,
                                content=content,
                                metadata=self._build_metadata(
                                    base_url, current_title, library, version
                                ),
                            )
                        )

                current_content = section
            else:
                current_title = section.strip()

        if current_title and current_content:
            content = re.sub(r"<[^>]+>", " ", current_content)
            content = re.sub(r"\s+", " ", content).strip()

            if content:
                chunks.append(
                    DocumentationChunk(
                        title=current_title,
                        content=content,
                        metadata=self._build_metadata(
                            base_url, current_title, library, version
                        ),
                    )
                )

        return chunks

    def _parse_markdown_documentation(
        self, markdown: str, library: str, version: str
    ) -> list[DocumentationChunk]:
        """Parse Markdown documentation into chunks."""
        chunks: list[DocumentationChunk] = []
        sections = re.split(r"(#+)\s+(.*)", markdown)

        current_level = 0
        current_title = ""
        current_content = ""

        for index in range(0, len(sections), 3):
            if index + 2 < len(sections):
                level = len(sections[index + 1])
                title = sections[index + 2].strip()
                content = sections[index + 3] if index + 3 < len(sections) else ""

                if current_title and (
                    level <= current_level or index + 3 >= len(sections)
                ):
                    if current_content.strip():
                        chunks.append(
                            DocumentationChunk(
                                title=current_title,
                                content=current_content.strip(),
                                metadata=self._build_metadata(
                                    f"https://pypi.org/project/{library}/{version}/",
                                    current_title,
                                    library,
                                    version,
                                ),
                            )
                        )

                current_level = level
                current_title = title
                current_content = content

        if current_title and current_content.strip():
            chunks.append(
                DocumentationChunk(
                    title=current_title,
                    content=current_content.strip(),
                    metadata=self._build_metadata(
                        f"https://pypi.org/project/{library}/{version}/",
                        current_title,
                        library,
                        version,
                    ),
                )
            )

        return chunks

    def _convert_docstrings_to_chunks(
        self, docstrings: Mapping[str, object], library: str, version: str
    ) -> list[DocumentationChunk]:
        """Convert extracted docstrings to documentation chunks."""
        chunks: list[DocumentationChunk] = []
        metadata_base = f"https://pypi.org/project/{library}/{version}/"

        modules = docstrings.get("modules", {})
        if isinstance(modules, Mapping):
            for module_name, module_data in modules.items():
                if isinstance(module_data, Mapping):
                    docstring = module_data.get("docstring", "")
                    if isinstance(docstring, str) and docstring:
                        chunks.append(
                            DocumentationChunk(
                                title=f"Module: {module_name}",
                                content=docstring,
                                metadata=self._build_metadata(
                                    metadata_base,
                                    "Modules",
                                    library,
                                    version,
                                    extra={"module": module_name},
                                ),
                            )
                        )

        classes = docstrings.get("classes", {})
        if isinstance(classes, Mapping):
            for class_name, class_data in classes.items():
                if isinstance(class_data, Mapping):
                    class_doc = class_data.get("docstring", "")
                    if isinstance(class_doc, str) and class_doc:
                        chunks.append(
                            DocumentationChunk(
                                title=f"Class: {class_name}",
                                content=class_doc,
                                metadata=self._build_metadata(
                                    metadata_base,
                                    "Classes",
                                    library,
                                    version,
                                    extra={"class": class_name},
                                ),
                            )
                        )

                    methods = class_data.get("methods", {})
                    if isinstance(methods, Mapping):
                        for method_name, method_data in methods.items():
                            if isinstance(method_data, Mapping):
                                method_doc = method_data.get("docstring", "")
                                if isinstance(method_doc, str) and method_doc:
                                    chunks.append(
                                        DocumentationChunk(
                                            title=f"Method: {class_name}.{method_name}",
                                            content=method_doc,
                                            metadata=self._build_metadata(
                                                metadata_base,
                                                "Methods",
                                                library,
                                                version,
                                                extra={
                                                    "class": class_name,
                                                    "method": method_name,
                                                },
                                            ),
                                        )
                                    )

        functions = docstrings.get("functions", {})
        if isinstance(functions, Mapping):
            for function_name, function_data in functions.items():
                if isinstance(function_data, Mapping):
                    func_doc = function_data.get("docstring", "")
                    if isinstance(func_doc, str) and func_doc:
                        chunks.append(
                            DocumentationChunk(
                                title=f"Function: {function_name}",
                                content=func_doc,
                                metadata=self._build_metadata(
                                    metadata_base,
                                    "Functions",
                                    library,
                                    version,
                                    extra={"function": function_name},
                                ),
                            )
                        )

        return chunks

    def _build_metadata(
        self,
        source_url: str,
        section: str,
        library: str,
        version: str,
        *,
        extra: Mapping[str, str] | None = None,
    ) -> Metadata:
        metadata: Metadata = {
            "source_url": source_url,
            "section": section,
            "library": library,
            "version": version,
        }
        if extra:
            for key, value in extra.items():
                metadata[key] = value
        return metadata

    def _get_docstring_extraction_script(self, library: str) -> str:
        """Get a Python script for extracting docstrings from a library."""
        return f"""
import json
import inspect
import importlib
import pkgutil
import sys

def extract_docstrings(library_name):
    result = {{
        "modules": {{}},
        "classes": {{}},
        "functions": {{}}
    }}

    try:
        library = importlib.import_module(library_name)

        result["modules"][library_name] = {{
            "docstring": inspect.getdoc(library) or ""
        }}

        for _, name, is_pkg in pkgutil.iter_modules(
            library.__path__, library.__name__ + '.'
        ):
            try:
                module = importlib.import_module(name)
                result["modules"][name] = {{
                    "docstring": inspect.getdoc(module) or ""
                }}

                for obj_name, obj in inspect.getmembers(module):
                    if obj_name.startswith('_'):
                        continue

                    if inspect.isclass(obj):
                        methods = {{}}
                        for method_name, method in inspect.getmembers(
                            obj, inspect.isfunction
                        ):
                            if not method_name.startswith('_'):
                                methods[method_name] = {{
                                    "docstring": inspect.getdoc(method) or ""
                                }}

                        result["classes"][obj.__name__] = {{
                            "docstring": inspect.getdoc(obj) or "",
                            "methods": methods
                        }}

                    elif inspect.isfunction(obj):
                        result["functions"][obj.__name__] = {{
                            "docstring": inspect.getdoc(obj) or ""
                        }}
            except Exception as exc:
                print(
                    f"Error processing module {{name}}: {{exc}}",
                    file=sys.stderr,
                )
    except Exception as exc:
        print(
            f"Failed to import library {{library_name}}: {{exc}}",
            file=sys.stderr,
        )

    return result

if __name__ == "__main__":
    docstrings = extract_docstrings("{library}")
    print(json.dumps(docstrings))
"""


class DocumentationFetcher:
    """
    Fetches documentation from various sources.

    This class provides methods for fetching documentation for libraries,
    frameworks, and languages from various sources, including official
    documentation sites, package repositories, and GitHub.
    """

    def __init__(self) -> None:
        """Initialize the documentation fetcher."""
        self.cache_dir = os.path.join(tempfile.gettempdir(), "devsynth_docs_cache")
        os.makedirs(self.cache_dir, exist_ok=True)

        self.sources: list[DocumentationSource] = [
            PyPIDocumentationSource(self._download)
        ]

        logger.info("Documentation fetcher initialized")

    def fetch_documentation(
        self, library: str, version: str, offline: bool = False
    ) -> list[DocumentationChunk]:
        """Fetch documentation for a library version."""
        cache_file = os.path.join(self.cache_dir, f"{library}_{version}.json")

        if os.path.exists(cache_file):
            try:
                with open(cache_file, encoding="utf-8") as cache_handle:
                    cached = json.load(cache_handle)
                if isinstance(cached, list):
                    return [
                        DocumentationChunk.from_json(item)
                        for item in cached
                        if isinstance(item, Mapping)
                    ]
            except Exception:  # pragma: no cover - defensive logging
                logger.warning(
                    "Failed to read cached documentation for %s %s", library, version
                )

        if offline:
            raise ValueError(f"No cached documentation for {library} {version}")

        for source in self.sources:
            if source.supports_library(library):
                chunks = source.fetch_documentation(library, version)
                if chunks:
                    try:
                        with open(cache_file, "w", encoding="utf-8") as cache_handle:
                            json.dump(
                                [chunk.to_json() for chunk in chunks], cache_handle
                            )
                    except Exception:  # pragma: no cover - caching best-effort
                        logger.debug(
                            "Failed to cache documentation for %s %s", library, version
                        )

                    logger.info(
                        "Fetched %s documentation chunks for %s %s",
                        len(chunks),
                        library,
                        version,
                    )
                    return chunks

        raise ValueError(f"No documentation source found for {library} {version}")

    def get_available_versions(self, library: str) -> list[str]:
        """Get available versions for a library."""
        versions: list[str] = []

        for source in self.sources:
            if source.supports_library(library):
                versions.extend(source.get_available_versions(library))

        unique_versions = sorted(set(versions), key=self._version_key)
        if not unique_versions:
            raise ValueError(f"No versions found for {library}")

        logger.info("Found %s available versions for %s", len(unique_versions), library)
        return unique_versions

    def supports_library(self, library: str) -> bool:
        """Check if any source supports a library."""
        return any(source.supports_library(library) for source in self.sources)

    def _version_key(self, version: str) -> tuple[int | str, ...]:
        """Convert a version string to a tuple for sorting."""
        parts: list[int | str] = []
        for part in version.split("."):
            try:
                parts.append(int(part))
            except ValueError:
                parts.append(part)
        return tuple(parts)

    def _download(self, url: str, *, timeout: float = 10) -> DownloadManifest:
        """Download a URL and return a :class:`DownloadManifest`."""
        try:
            response = requests.get(url, timeout=timeout)
        except requests.RequestException as exc:
            logger.debug("Network error when fetching %s: %s", url, exc)
            return DownloadManifest(url=url, success=False, error=str(exc))

        if response.status_code != 200:
            logger.debug(
                "Unexpected status %s when fetching %s", response.status_code, url
            )
            return DownloadManifest(
                url=url,
                success=False,
                status_code=response.status_code,
                error=f"status_code={response.status_code}",
            )

        return DownloadManifest(
            url=url,
            success=True,
            status_code=response.status_code,
            content=response.text,
        )
