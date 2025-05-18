
from typing import Any, Dict, List, Optional
from ...domain.interfaces.llm import LLMProvider, LLMProviderFactory
from ...application.llm.providers import SimpleLLMProviderFactory, OpenAIProvider, AnthropicProvider

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError

class LLMBackendAdapter:
    """Adapter for LLM backends."""
    
    def __init__(self):
        self.factory = SimpleLLMProviderFactory()
    
    def create_provider(self, provider_type: str, config: Dict[str, Any] = None) -> LLMProvider:
        """Create an LLM provider of the specified type."""
        return self.factory.create_provider(provider_type, config)
    
    def register_provider_type(self, provider_type: str, provider_class: type) -> None:
        """Register a new provider type."""
        self.factory.register_provider_type(provider_type, provider_class)
