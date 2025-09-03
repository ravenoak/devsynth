import os
import time
from unittest.mock import patch

import pytest


@pytest.mark.fast
def test_health_check_succeeds_when_sync_api_lists_models(monkeypatch):
    """ReqID: LMSTUDIO-HC-1
    When sync_api.list_downloaded_models returns, health_check should be True.
    """
    # Ensure resource flag is enabled so health_check runs
    monkeypatch.setenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "true")

    from devsynth.application.llm.lmstudio_provider import LMStudioProvider

    provider = LMStudioProvider({"auto_select_model": False})

    # Patch list_downloaded_models to return non-empty list quickly
    with patch(
        "devsynth.application.llm.lmstudio_provider.lmstudio.sync_api.list_downloaded_models",
        return_value=[type("M", (), {"model_key": "m", "display_name": "M"})()],
    ):
        assert provider.health_check() is True


@pytest.mark.fast
def test_health_check_bounded_retry_and_returns_false_on_failure(monkeypatch):
    """ReqID: LMSTUDIO-HC-2
    If sync_api.list_downloaded_models keeps failing, health_check returns False within ~5s budget.
    """
    monkeypatch.setenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "true")
    # Keep retries small and timeout small to speed up
    monkeypatch.setenv("DEVSYNTH_LMSTUDIO_RETRIES", "3")
    monkeypatch.setenv("DEVSYNTH_LMSTUDIO_TIMEOUT_SECONDS", "0.4")

    from devsynth.application.llm.lmstudio_provider import LMStudioProvider

    provider = LMStudioProvider({"auto_select_model": False})

    call_count = {"n": 0}

    def _boom(kind: str):  # noqa: ARG001
        call_count["n"] += 1
        raise RuntimeError("unreachable")

    with (
        patch(
            "devsynth.application.llm.lmstudio_provider.lmstudio.sync_api.list_downloaded_models",
            side_effect=_boom,
        ),
        patch(
            "devsynth.application.llm.lmstudio_provider.lmstudio.sync_api.configure_default_client",
            return_value=None,
        ),
    ):
        t0 = time.perf_counter()
        ok = provider.health_check()
        duration = time.perf_counter() - t0
        assert ok is False
        assert duration <= 5.5  # bounded by implementation budget
        assert call_count["n"] >= 1
