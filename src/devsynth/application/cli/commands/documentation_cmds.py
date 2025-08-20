"""Register documentation-related CLI commands."""

from ..registry import register
from .generate_docs_cmd import generate_docs_cmd

register("generate-docs", generate_docs_cmd)

__all__ = ["generate_docs_cmd"]
