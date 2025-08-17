from __future__ import annotations

import pytest

pytestmark = [pytest.mark.fast]


def test_lmstudio_service_fixture_returns_base_url(lmstudio_service):
    """Ensure the mock service fixture provides a usable base URL."""
    assert lmstudio_service.base_url
