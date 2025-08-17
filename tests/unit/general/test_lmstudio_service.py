from __future__ import annotations

import pytest

pytestmark = [pytest.mark.fast]


def test_lmstudio_mock_fixture_returns_base_url(lmstudio_mock):
    """Ensure the mock service fixture provides a usable base URL."""
    assert lmstudio_mock.base_url
