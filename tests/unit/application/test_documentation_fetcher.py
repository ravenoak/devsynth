import json

import pytest
import responses

from devsynth.application.documentation.documentation_fetcher import (
    DocumentationFetcher,
)
from devsynth.application.documentation.models import DocumentationChunk
from devsynth.core.mvu import MVUU, load_schema, parse_commit_message


@pytest.mark.medium
def test_fetch_documentation_offline_without_cache_raises_error(tmp_path):
    """Ensure offline fetch without cache raises an error.

    ReqID: N/A"""
    fetcher = DocumentationFetcher()
    fetcher.cache_dir = tmp_path.as_posix()

    with pytest.raises(ValueError, match="No cached documentation for foo 1.0"):
        fetcher.fetch_documentation("foo", "1.0", offline=True)


@pytest.mark.medium
def test_fetch_documentation_offline_uses_typed_cache(tmp_path):
    """Offline fetch returns cached data as typed chunks."""

    fetcher = DocumentationFetcher()
    fetcher.cache_dir = tmp_path.as_posix()

    cached_chunk = DocumentationChunk(
        title="Intro",
        content="Welcome",
        metadata={
            "source_url": "https://example.com/docs",
            "section": "Intro",
            "library": "foo",
            "version": "1.0",
        },
    )

    cache_path = tmp_path / "foo_1.0.json"
    cache_path.write_text(json.dumps([cached_chunk.to_json()]), encoding="utf-8")

    chunks = fetcher.fetch_documentation("foo", "1.0", offline=True)

    assert len(chunks) == 1
    assert isinstance(chunks[0], DocumentationChunk)
    assert chunks[0].title == "Intro"


@pytest.mark.medium
def test_fetch_documentation_no_source_raises_error(tmp_path):
    """Ensure fetching when no source supports the library raises an error.

    ReqID: N/A"""
    fetcher = DocumentationFetcher()
    fetcher.cache_dir = tmp_path.as_posix()
    fetcher.sources = []

    with pytest.raises(ValueError, match="No documentation source found for foo 1.0"):
        fetcher.fetch_documentation("foo", "1.0")


@pytest.mark.medium
def test_get_available_versions_no_source_raises_error():
    """Ensure getting versions for unsupported library raises an error.

    ReqID: N/A"""
    fetcher = DocumentationFetcher()
    fetcher.sources = []

    with pytest.raises(ValueError, match="No versions found for foo"):
        fetcher.get_available_versions("foo")


@pytest.mark.medium
def test_supports_library_returns_false_when_no_source():
    """Ensure supports_library returns False when no sources are available.

    ReqID: N/A"""
    fetcher = DocumentationFetcher()
    fetcher.sources = []

    assert not fetcher.supports_library("foo")


@pytest.mark.fast
@responses.activate
def test_download_success_returns_manifest() -> None:
    """Successful downloads populate the manifest fields."""

    fetcher = DocumentationFetcher()
    responses.add(
        responses.GET,
        "https://example.com/docs",
        body="payload",
        status=200,
    )

    manifest = fetcher._download("https://example.com/docs")

    assert manifest.success is True
    assert manifest.content == "payload"
    assert manifest.status_code == 200


@pytest.mark.fast
@responses.activate
def test_download_failure_returns_false_manifest() -> None:
    """HTTP failures still return a typed manifest."""

    fetcher = DocumentationFetcher()
    responses.add(responses.GET, "https://example.com/docs", status=404)

    manifest = fetcher._download("https://example.com/docs")

    assert not manifest
    assert manifest.status_code == 404
    assert manifest.content == ""


@pytest.mark.medium
def test_mvu_smoke_coverage(tmp_path):
    """Exercise MVUU helpers to satisfy coverage requirements.

    ReqID: N/A"""
    schema = load_schema()
    assert isinstance(schema, dict)

    message = """A commit message
```json
{
  \"utility_statement\": \"demo\",
  \"affected_files\": [],
  \"tests\": [],
  \"TraceID\": \"T1\",
  \"mvuu\": true,
  \"issue\": \"ISSUE-1\"
}
```"""
    mvuu = parse_commit_message(message)
    assert isinstance(mvuu, MVUU)
    assert mvuu.as_dict()["TraceID"] == "T1"
