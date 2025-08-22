from __future__ import annotations

import pytest

pytest.importorskip("lmstudio")

pytestmark = [pytest.mark.fast, pytest.mark.requires_resource("lmstudio")]


def test_lmstudio_mock_fixture_returns_base_url(lmstudio_mock):
    """Ensure the mock service fixture provides a usable base URL.

    ReqID: LMSTUDIO-1"""
    assert lmstudio_mock.base_url
