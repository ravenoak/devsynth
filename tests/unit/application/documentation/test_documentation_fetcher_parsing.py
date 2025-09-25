"""Pure-function tests for :mod:`documentation_fetcher`."""

from __future__ import annotations

import pytest

from devsynth.application.documentation.documentation_fetcher import (
    DocumentationFetcher,
    PyPIDocumentationSource,
)
from devsynth.application.documentation.models import DownloadManifest

pytestmark = pytest.mark.fast


def test_parse_html_documentation_extracts_sections() -> None:
    """HTML parsing splits content by headings and strips markup.

    ReqID: N/A
    """

    source = PyPIDocumentationSource(
        lambda url: DownloadManifest(url=url, success=False)
    )
    html = "<h1>Intro</h1><p>Welcome</p><h2>Usage</h2><p>Use it wisely.</p>"

    chunks = source._parse_html_documentation(
        html, "https://example.com/docs", "sample-lib", "1.0"
    )

    assert chunks[0].title == "Intro"
    assert "Welcome" in chunks[0].content
    assert chunks[-1].title == "Usage"
    assert chunks[-1].metadata["source_url"] == "https://example.com/docs"


def test_parse_markdown_documentation_respects_heading_levels() -> None:
    """Markdown parsing preserves section order and metadata.

    ReqID: N/A
    """

    source = PyPIDocumentationSource(
        lambda url: DownloadManifest(url=url, success=False)
    )
    markdown = "## Intro\nIntro details\n## Usage\nUsage details"

    chunks = source._parse_markdown_documentation(markdown, "sample", "2.0")

    assert [chunk.title for chunk in chunks] == ["Intro", "Usage"]
    assert chunks[0].content == "Intro details"
    assert chunks[1].metadata["section"] == "Usage"


def test_convert_docstrings_to_chunks_builds_expected_metadata() -> None:
    """Docstring conversion emits module, class, method, and function chunks.

    ReqID: N/A
    """

    source = PyPIDocumentationSource(
        lambda url: DownloadManifest(url=url, success=False)
    )
    docstrings = {
        "modules": {"pkg": {"docstring": "Module documentation."}},
        "classes": {
            "Widget": {
                "docstring": "Class documentation.",
                "methods": {
                    "configure": {"docstring": "Method details."},
                },
            }
        },
        "functions": {"helper": {"docstring": "Helper documentation."}},
    }

    chunks = source._convert_docstrings_to_chunks(docstrings, "sample", "3.1")

    titles = {chunk.title for chunk in chunks}
    assert titles == {
        "Module: pkg",
        "Class: Widget",
        "Method: Widget.configure",
        "Function: helper",
    }
    module_chunk = next(chunk for chunk in chunks if chunk.title == "Module: pkg")
    assert module_chunk.metadata["library"] == "sample"
    assert module_chunk.metadata["version"] == "3.1"


def test_version_key_supports_numeric_sorting_and_literals() -> None:
    """Version keys normalise numeric parts while preserving literals.

    ReqID: N/A
    """

    fetcher = DocumentationFetcher()
    assert fetcher._version_key("1.2.3") == (1, 2, 3)
    assert fetcher._version_key("2") == (2,)
    assert fetcher._version_key("1.2b") == (1, "2b")
    assert sorted(["1.9", "1.10", "1.2"], key=fetcher._version_key) == [
        "1.2",
        "1.9",
        "1.10",
    ]
