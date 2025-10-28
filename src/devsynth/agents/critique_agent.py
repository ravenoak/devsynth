"""Simple critique agent for reviewing code or test outputs."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import List

from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


@dataclass
class Critique:
    """Result returned by :class:`CritiqueAgent`."""

    approved: bool
    issues: list[str]


class CritiqueAgent:
    """Agent that provides lightweight feedback on generated artifacts.

    The agent inspects source code or test output and returns a
    :class:`Critique` describing potential problems.
    """

    def review(self, content: str) -> Critique:
        """Analyze ``content`` and return a :class:`Critique`.

        The review currently performs very small heuristics:

        * Flags unfinished work marked with ``TODO``.
        * Detects failing tests via ``FAIL`` or ``error`` keywords.
        * Warns when a function definition lacks a docstring.
        """
        issues: list[str] = []
        lower = content.lower()

        if "todo" in lower:
            issues.append("Found TODO marker indicating unfinished work.")
        if "fail" in lower or "error" in lower:
            issues.append("Test failures or errors detected.")

        try:
            tree = ast.parse(content)
        except SyntaxError:
            logger.debug("Skipping docstring check; invalid syntax")
        else:
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if ast.get_docstring(node) is None:
                        issues.append(f"Function '{node.name}' missing docstring.")

        logger.debug("Critique issues: %s", issues)
        return Critique(approved=not issues, issues=issues)
