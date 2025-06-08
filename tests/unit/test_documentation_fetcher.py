import pytest

from devsynth.application.documentation.documentation_fetcher import (
    DocumentationFetcher,
)


def test_fetcher_initialization():
    fetcher = DocumentationFetcher()
    assert fetcher.sources
