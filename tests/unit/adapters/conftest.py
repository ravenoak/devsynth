from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def _lmstudio_stub(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    """Provide a patched ``lmstudio`` module and opt into LM Studio resource tests.

    Tests under ``tests/unit/adapters`` rely on LM Studio provider behavior but
    should not import the real optional dependency or require the actual
    service.  This autouse fixture injects a lightweight module stub into
    ``sys.modules`` and sets the resource flag so provider code paths execute
    without hitting the network.
    """

    module = types.ModuleType("lmstudio")
    module.llm = MagicMock(name="lmstudio.llm")
    module.embedding_model = MagicMock(name="lmstudio.embedding_model")
    module.sync_api = types.SimpleNamespace(
        configure_default_client=MagicMock(
            name="lmstudio.sync_api.configure_default_client"
        ),
        list_downloaded_models=MagicMock(
            name="lmstudio.sync_api.list_downloaded_models"
        ),
    )

    monkeypatch.setitem(sys.modules, "lmstudio", module)
    monkeypatch.setenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "1")
    return module
