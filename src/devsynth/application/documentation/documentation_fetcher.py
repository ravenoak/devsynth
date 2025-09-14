"""
Documentation Fetcher module.

This module defines the DocumentationFetcher class for fetching documentation
from various sources, including official documentation sites, PyPI, and GitHub.
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
from abc import ABC, abstractmethod
from typing import Any, cast

import requests

from devsynth.logging_setup import DevSynthLogger

# Create a logger for this module
logger = DevSynthLogger(__name__)


class DocumentationSource(ABC):
    """Abstract base class for documentation sources."""

    @abstractmethod
    def fetch_documentation(
        self, library: str, version: str, offline: bool = False
    ) -> list[dict[str, Any]]:
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

    def __init__(self) -> None:
        """Initialize the PyPI documentation source."""
        self.cache_dir = os.path.join(tempfile.gettempdir(), "devsynth_docs_cache")
        os.makedirs(self.cache_dir, exist_ok=True)

    def fetch_documentation(
        self, library: str, version: str, offline: bool = False
    ) -> list[dict[str, Any]]:
        """Fetch documentation for a Python library."""
        logger.info(
            f"Fetching documentation for {library} {version} from PyPI/ReadTheDocs"
        )

        # Try to get documentation from ReadTheDocs first
        chunks = self._fetch_from_readthedocs(library, version)
        if chunks:
            return chunks

        # Fall back to PyPI documentation
        chunks = self._fetch_from_pypi(library, version)
        if chunks:
            return chunks

        # If all else fails, try to extract docstrings from the package
        return self._extract_docstrings(library, version)

    def supports_library(self, library: str) -> bool:
        """Check if this source supports a library."""
        # Try to find the library on PyPI
        try:
            response = requests.get(f"https://pypi.org/pypi/{library}/json", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Error checking PyPI for {library}: {str(e)}")
            return False

    def get_available_versions(self, library: str) -> list[str]:
        """Get available versions for a library from PyPI."""
        try:
            response = requests.get(f"https://pypi.org/pypi/{library}/json", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return list(data.get("releases", {}).keys())
            return []
        except Exception as e:
            logger.warning(f"Error getting versions for {library} from PyPI: {str(e)}")
            return []

    def _fetch_from_readthedocs(
        self, library: str, version: str
    ) -> list[dict[str, Any]]:
        """Fetch documentation from ReadTheDocs."""
        # Try common ReadTheDocs URL patterns
        urls = [
            f"https://{library}.readthedocs.io/en/{version}/",
            f"https://{library}.readthedocs.io/en/v{version}/",
            f"https://readthedocs.org/projects/{library}/versions/{version}/",
        ]

        for url in urls:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    return self._parse_html_documentation(
                        response.text, url, library, version
                    )
            except Exception as e:
                logger.debug(f"Error fetching from ReadTheDocs URL {url}: {str(e)}")

        return []

    def _fetch_from_pypi(self, library: str, version: str) -> list[dict[str, Any]]:
        """Fetch documentation from PyPI."""
        try:
            response = requests.get(
                f"https://pypi.org/pypi/{library}/{version}/json", timeout=10
            )
            if response.status_code == 200:
                data = response.json()

                # Check for documentation URL in project URLs
                project_urls = data.get("info", {}).get("project_urls", {})
                doc_url = project_urls.get("Documentation")

                if doc_url:
                    try:
                        doc_response = requests.get(doc_url, timeout=10)
                        if doc_response.status_code == 200:
                            return self._parse_html_documentation(
                                doc_response.text, doc_url, library, version
                            )
                    except Exception as e:
                        logger.debug(
                            f"Error fetching from documentation URL {doc_url}: {str(e)}"
                        )

                # Check for documentation in the long description
                description = data.get("info", {}).get("description", "")
                if description:
                    return self._parse_markdown_documentation(
                        description, library, version
                    )

            return []
        except Exception as e:
            logger.warning(
                f"Error fetching from PyPI for {library} {version}: {str(e)}"
            )
            return []

    def _extract_docstrings(self, library: str, version: str) -> list[dict[str, Any]]:
        """Extract docstrings from a Python package."""
        logger.info(f"Attempting to extract docstrings from {library} {version}")

        # Create a temporary virtual environment
        venv_dir = os.path.join(self.cache_dir, f"{library}_{version}_venv")
        if os.path.exists(venv_dir):
            shutil.rmtree(venv_dir)

        try:
            # Create virtual environment
            subprocess.run(["python", "-m", "venv", venv_dir], check=True)

            # Install the package
            pip_path = (
                os.path.join(venv_dir, "bin", "pip")
                if os.name != "nt"
                else os.path.join(venv_dir, "Scripts", "pip.exe")
            )
            subprocess.run([pip_path, "install", f"{library}=={version}"], check=True)

            # Run a script to extract docstrings
            python_path = (
                os.path.join(venv_dir, "bin", "python")
                if os.name != "nt"
                else os.path.join(venv_dir, "Scripts", "python.exe")
            )

            # Create a temporary script to extract docstrings
            script_path = os.path.join(
                self.cache_dir, f"extract_docstrings_{library}_{version}.py"
            )
            with open(script_path, "w") as f:
                f.write(self._get_docstring_extraction_script(library))

            # Run the script
            result = subprocess.run(
                [python_path, script_path], capture_output=True, text=True, check=False
            )

            # Parse the output
            if result.returncode == 0 and result.stdout:
                try:
                    docstrings = json.loads(result.stdout)
                    return self._convert_docstrings_to_chunks(
                        docstrings, library, version
                    )
                except json.JSONDecodeError:
                    logger.error(
                        f"Error parsing docstring output for {library} {version}"
                    )

            return []
        except Exception as e:
            logger.error(
                f"Error extracting docstrings for {library} {version}: {str(e)}"
            )
            return []
        finally:
            # Clean up
            if os.path.exists(venv_dir):
                shutil.rmtree(venv_dir)
            if os.path.exists(script_path):
                os.remove(script_path)

    def _parse_html_documentation(
        self, html: str, base_url: str, library: str, version: str
    ) -> list[dict[str, Any]]:
        """Parse HTML documentation into chunks."""
        # Simplistic implementation; a full HTML parser could improve accuracy
        chunks = []

        # Split by headings
        sections = re.split(r"<h[1-3][^>]*>(.*?)</h[1-3]>", html)

        current_title = ""
        current_content = ""

        for i, section in enumerate(sections):
            if i % 2 == 0:
                # This is content
                if current_title:
                    # Clean HTML tags
                    content = re.sub(r"<[^>]+>", " ", section)
                    content = re.sub(r"\s+", " ", content).strip()

                    if content:
                        chunks.append(
                            {
                                "title": current_title,
                                "content": content,
                                "metadata": {
                                    "source_url": base_url,
                                    "section": current_title,
                                    "library": library,
                                    "version": version,
                                },
                            }
                        )

                current_content = section
            else:
                # This is a heading
                current_title = section.strip()

        # Add the last section
        if current_title and current_content:
            # Clean HTML tags
            content = re.sub(r"<[^>]+>", " ", current_content)
            content = re.sub(r"\s+", " ", content).strip()

            if content:
                chunks.append(
                    {
                        "title": current_title,
                        "content": content,
                        "metadata": {
                            "source_url": base_url,
                            "section": current_title,
                            "library": library,
                            "version": version,
                        },
                    }
                )

        return chunks

    def _parse_markdown_documentation(
        self, markdown: str, library: str, version: str
    ) -> list[dict[str, Any]]:
        """Parse Markdown documentation into chunks."""
        chunks = []

        # Split by headings
        sections = re.split(r"(#+)\s+(.*)", markdown)

        current_level = 0
        current_title = ""
        current_content = ""

        for i in range(0, len(sections), 3):
            if i + 2 < len(sections):
                level = len(sections[i + 1])
                title = sections[i + 2].strip()
                content = sections[i + 3] if i + 3 < len(sections) else ""

                if current_title and (level <= current_level or i + 3 >= len(sections)):
                    # Save the previous section
                    if current_content.strip():
                        chunks.append(
                            {
                                "title": current_title,
                                "content": current_content.strip(),
                                "metadata": {
                                    "source_url": (
                                        f"https://pypi.org/project/{library}/{version}/"
                                    ),
                                    "section": current_title,
                                    "library": library,
                                    "version": version,
                                },
                            }
                        )

                current_level = level
                current_title = title
                current_content = content

        # Add the last section
        if current_title and current_content.strip():
            chunks.append(
                {
                    "title": current_title,
                    "content": current_content.strip(),
                    "metadata": {
                        "source_url": (
                            f"https://pypi.org/project/{library}/{version}/"
                        ),
                        "section": current_title,
                        "library": library,
                        "version": version,
                    },
                }
            )

        return chunks

    def _convert_docstrings_to_chunks(
        self, docstrings: dict[str, Any], library: str, version: str
    ) -> list[dict[str, Any]]:
        """Convert extracted docstrings to documentation chunks."""
        chunks = []

        # Process module docstrings
        for module_name, module_data in docstrings.get("modules", {}).items():
            docstring = module_data.get("docstring", "")
            if docstring:
                chunks.append(
                    {
                        "title": f"Module: {module_name}",
                        "content": docstring,
                        "metadata": {
                            "source_url": (
                                f"https://pypi.org/project/{library}/{version}/"
                            ),
                            "section": "Modules",
                            "library": library,
                            "version": version,
                            "module": module_name,
                        },
                    }
                )

        # Process class docstrings
        for class_name, class_data in docstrings.get("classes", {}).items():
            docstring = class_data.get("docstring", "")
            if docstring:
                chunks.append(
                    {
                        "title": f"Class: {class_name}",
                        "content": docstring,
                        "metadata": {
                            "source_url": (
                                f"https://pypi.org/project/{library}/{version}/"
                            ),
                            "section": "Classes",
                            "library": library,
                            "version": version,
                            "class": class_name,
                        },
                    }
                )

            # Process method docstrings
            for method_name, method_data in class_data.get("methods", {}).items():
                docstring = method_data.get("docstring", "")
                if docstring:
                    chunks.append(
                        {
                            "title": f"Method: {class_name}.{method_name}",
                            "content": docstring,
                            "metadata": {
                                "source_url": (
                                    f"https://pypi.org/project/{library}/{version}/"
                                ),
                                "section": "Methods",
                                "library": library,
                                "version": version,
                                "class": class_name,
                                "method": method_name,
                            },
                        }
                    )

        # Process function docstrings
        for function_name, function_data in docstrings.get("functions", {}).items():
            docstring = function_data.get("docstring", "")
            if docstring:
                chunks.append(
                    {
                        "title": f"Function: {function_name}",
                        "content": docstring,
                        "metadata": {
                            "source_url": (
                                f"https://pypi.org/project/{library}/{version}/"
                            ),
                            "section": "Functions",
                            "library": library,
                            "version": version,
                            "function": function_name,
                        },
                    }
                )

        return chunks

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
        # Import the library
        library = importlib.import_module(library_name)

        # Extract module docstring
        result["modules"][library_name] = {{
            "docstring": inspect.getdoc(library) or ""
        }}

        # Find all submodules
        for _, name, is_pkg in pkgutil.iter_modules(
            library.__path__, library.__name__ + '.'
        ):
            try:
                module = importlib.import_module(name)
                result["modules"][name] = {{
                    "docstring": inspect.getdoc(module) or ""
                }}

                # Extract classes and functions
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
            except Exception as e:
                print(
                    f"Error processing module {{name}}: {{e}}",
                    file=sys.stderr,
                )
    except Exception as e:
        print(
            f"Failed to import library {{library_name}}: {{e}}",
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
        self.sources: list[DocumentationSource] = [PyPIDocumentationSource()]

        # Directory for caching fetched documentation
        self.cache_dir = os.path.join(tempfile.gettempdir(), "devsynth_docs_cache")
        os.makedirs(self.cache_dir, exist_ok=True)

        logger.info("Documentation fetcher initialized")

    def fetch_documentation(
        self, library: str, version: str, offline: bool = False
    ) -> list[dict[str, Any]]:
        """Fetch documentation for a library version.

        Args:
            library: The name of the library.
            version: The version of the library.
            offline: If ``True`` the method will only return cached
                documentation and will not attempt any network calls.

        Returns:
            A list of documentation chunks.

        Raises:
            ValueError: If ``offline`` is ``True`` and no cached documentation is
                available or if no source supports the requested library.
        """

        cache_file = os.path.join(self.cache_dir, f"{library}_{version}.json")

        # Return cached documentation if available
        if os.path.exists(cache_file):
            try:
                with open(cache_file, encoding="utf-8") as f:
                    return cast(list[dict[str, Any]], json.load(f))
            except Exception:
                logger.warning("Failed to read cached documentation")

        if offline:
            raise ValueError(f"No cached documentation for {library} {version}")

        # Find a source that supports the library
        for source in self.sources:
            if source.supports_library(library):
                chunks = source.fetch_documentation(library, version)
                if chunks:
                    # Cache the result for future offline use
                    try:
                        with open(cache_file, "w", encoding="utf-8") as f:
                            json.dump(chunks, f)
                    except Exception:
                        logger.debug("Failed to cache documentation")

                    logger.info(
                        f"Fetched {len(chunks)} documentation chunks for {library}"
                        f" {version}"
                    )
                    return chunks

        raise ValueError(f"No documentation source found for {library} {version}")

    def get_available_versions(self, library: str) -> list[str]:
        """
        Get available versions for a library.

        Args:
            library: The name of the library

        Returns:
            A list of available versions
        """
        versions = []

        for source in self.sources:
            if source.supports_library(library):
                source_versions = source.get_available_versions(library)
                versions.extend(source_versions)

        # Remove duplicates and sort
        versions = sorted(list(set(versions)), key=self._version_key)

        if not versions:
            raise ValueError(f"No versions found for {library}")

        logger.info(f"Found {len(versions)} available versions for {library}")
        return versions

    def supports_library(self, library: str) -> bool:
        """
        Check if any source supports a library.

        Args:
            library: The name of the library

        Returns:
            True if the library is supported, False otherwise
        """
        for source in self.sources:
            if source.supports_library(library):
                return True
        return False

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
