"""Tool registry for agent functions."""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


class ToolRegistry:
    """Registry mapping tool names to callables and metadata."""

    def __init__(self) -> None:
        """Initialize the tool registry."""
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        name: str,
        func: Callable[..., Any],
        description: str,
        parameters: Dict[str, Any],
    ) -> None:
        """Register a tool with its callable and metadata."""
        self._tools[name] = {
            "func": func,
            "description": description,
            "parameters": parameters,
        }
        logger.debug("Registered tool %s", name)

    def get(self, name: str) -> Optional[Callable[..., Any]]:
        """Return the callable for a registered tool."""
        tool = self._tools.get(name)
        return tool["func"] if tool else None

    def get_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """Return metadata for a registered tool."""
        tool = self._tools.get(name)
        if tool:
            return {
                "description": tool["description"],
                "parameters": tool["parameters"],
            }
        return None

    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """Return a copy of all registered tools and metadata."""
        return self._tools.copy()


# Global registry instance
_tool_registry = ToolRegistry()

# Export for direct import
tool_registry = _tool_registry


def get_tool_registry() -> ToolRegistry:
    """Return the global tool registry."""
    return _tool_registry
