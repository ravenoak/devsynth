import pytest

from devsynth.application.documentation.documentation_fetcher import (
    DocumentationFetcher,
)


def test_fetcher_initialization_succeeds():
    """Test that fetcher initialization succeeds.

    ReqID: N/A"""
    fetcher = DocumentationFetcher()
    assert fetcher.sources
