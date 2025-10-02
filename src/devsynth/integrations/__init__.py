"""Integration interfaces for external research providers."""

from __future__ import annotations

from .a2a import A2AConnector, StubA2AConnector
from .mcp import MCPConnector, StubMCPConnector

__all__ = [
    "A2AConnector",
    "MCPConnector",
    "StubA2AConnector",
    "StubMCPConnector",
]
