import pytest

from devsynth.application.documentation.documentation_fetcher import (
    DocumentationFetcher,
)
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
