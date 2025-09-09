"""
Documentation Ingestion Manager Module

This module re-exports the DocumentationIngestionManager class from the ingestion module
for backward compatibility.
"""

from .ingestion import DocumentationIngestionError, DocumentationIngestionManager

__all__ = ["DocumentationIngestionManager", "DocumentationIngestionError"]
