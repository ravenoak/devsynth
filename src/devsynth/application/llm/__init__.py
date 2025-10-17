"""LLM provider utilities."""

from typing import Any, Dict

# Import get_llm_settings lazily to avoid import issues during testing
from devsynth.core.config_loader import load_config
from devsynth.logging_setup import DevSynthLogger

from .providers import factory as _factory


def get_llm_provider(config: Dict[str, Any] | None = None):
    """Return an LLM provider based on configuration.

    When ``offline_mode`` is enabled in the configuration the ``OfflineProvider``
    is selected regardless of the default provider in ``llm`` settings. This
    mirrors the behaviour described in the documentation and ensures repeatable
    operation when network access is unavailable.
    """

    cfg = config or load_config().as_dict()
    offline = cfg.get("offline_mode", False)

    from devsynth.config.settings import get_llm_settings
    llm_cfg = get_llm_settings()
    if "offline_provider" in cfg:
        llm_cfg["offline_provider"] = cfg["offline_provider"]

    provider_type = "offline" if offline else llm_cfg.get("provider", "openai")
    return _factory.create_provider(provider_type, llm_cfg)


def factory():
    return _factory


# Create a logger for this module
logger = DevSynthLogger(__name__)

__all__ = ["factory", "get_llm_provider"]
