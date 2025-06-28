"""LLM provider utilities."""

from typing import Dict, Any

from devsynth.logging_setup import DevSynthLogger
from devsynth.exceptions import DevSynthError
from devsynth.config import load_project_config, get_llm_settings

from .providers import factory

# Import local provider so it is registered
from . import local_provider  # noqa: F401

# Create a logger for this module
logger = DevSynthLogger(__name__)


def get_llm_provider(config: Dict[str, Any] | None = None):
    """Return an LLM provider based on configuration.

    When ``offline_mode`` is ``True`` in the project configuration the local
    provider is selected regardless of the configured provider type.
    """

    cfg = config or load_project_config().config.as_dict()
    offline = cfg.get("offline_mode", False)

    llm_cfg = get_llm_settings()
    provider_type = "local" if offline else llm_cfg.get("provider", "openai")
    return factory.create_provider(provider_type, llm_cfg)
