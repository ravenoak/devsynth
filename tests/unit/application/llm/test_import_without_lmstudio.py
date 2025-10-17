import importlib
import sys

import pytest


@pytest.mark.medium
def test_import_lmstudio_provider_without_lmstudio_succeeds():
    """Importing providers should succeed without lmstudio installed.

    ReqID: LMSTUDIO-2"""
    # Remove modules from sys.modules to force reimport
    sys.modules.pop("devsynth.application.llm.providers", None)
    sys.modules.pop("devsynth.application.llm.lmstudio_provider", None)
    sys.modules.pop("lmstudio", None)

    # Set lmstudio module to None to simulate it not being available
    sys.modules["lmstudio"] = None

    providers = importlib.import_module("devsynth.application.llm.providers")
    assert providers.LMStudioProvider is None
    assert "lmstudio" not in providers.factory.provider_types


@pytest.mark.medium
def test_factory_missing_lmstudio_provider_raises_clear_error():
    """Requesting LM Studio provider without SDK yields a helpful error.

    ReqID: LMSTUDIO-3"""
    # Remove modules from sys.modules to force reimport
    sys.modules.pop("devsynth.application.llm.providers", None)
    sys.modules.pop("devsynth.application.llm.lmstudio_provider", None)
    sys.modules.pop("lmstudio", None)

    # Set lmstudio module to None to simulate it not being available
    sys.modules["lmstudio"] = None

    providers = importlib.import_module("devsynth.application.llm.providers")
    with pytest.raises(
        providers.ValidationError, match="LMStudio provider is unavailable"
    ):
        providers.factory.create_provider("lmstudio")
