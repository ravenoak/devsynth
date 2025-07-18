import logging
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.llm.offline_provider import OfflineProvider
from devsynth.application.llm.lmstudio_provider import LMStudioProvider


def test_provider_logging_cleanup(capsys):
    """Providers should not log after logging.shutdown."""
    OfflineProvider().generate("hello")
    with (
        patch("devsynth.application.llm.lmstudio_provider.lmstudio.llm") as mock_llm,
        patch(
            "devsynth.application.llm.lmstudio_provider.TokenTracker"
        ) as mock_tracker,
    ):
        mock_model = MagicMock()
        mock_model.complete.return_value = MagicMock(content="ok")
        mock_llm.return_value = mock_model
        mock_tracker.return_value.count_tokens.return_value = 1
        mock_tracker.return_value.ensure_token_limit.return_value = None
        provider = LMStudioProvider({"auto_select_model": False})
        provider.generate("hi")

    import lmstudio.sync_api as sync_api

    sync_api._reset_default_client()
    logging.shutdown()
    assert "I/O operation on closed file" not in capsys.readouterr().err
