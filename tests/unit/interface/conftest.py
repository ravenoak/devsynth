from __future__ import annotations

import pytest

from tests import conftest as root_conftest


@pytest.fixture
def force_webui_available(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure WebUI-gated tests run against the lightweight stub configuration."""
    monkeypatch.setenv("DEVSYNTH_RESOURCE_WEBUI_AVAILABLE", "1")
    monkeypatch.setattr(root_conftest, "is_webui_available", lambda: True)
