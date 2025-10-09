"""Integration interfaces for external research providers."""

from __future__ import annotations

from .a2a import A2AConnector, AutoresearchA2AConnector, StubA2AConnector
from .autoresearch_client import CONNECTORS_ENABLED_ENV, AutoresearchClient
from .mcp import (
    AUTORESEARCH_API_BASE_ENV,
    AutoresearchMCPConnector,
    MCPConnector,
    StubMCPConnector,
)

__all__ = [
    "A2AConnector",
    "AutoresearchA2AConnector",
    "AutoresearchClient",
    "AutoresearchMCPConnector",
    "AUTORESEARCH_API_BASE_ENV",
    "CONNECTORS_ENABLED_ENV",
    "MCPConnector",
    "StubA2AConnector",
    "StubMCPConnector",
]
