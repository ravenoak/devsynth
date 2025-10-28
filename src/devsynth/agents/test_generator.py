"""Prompt utilities for generating edge-case aware tests.

This module exposes helpers that load prompt templates used when requesting
new tests from language models. The templates live under
``application/prompts/templates/test_generation`` and cover boundary values
and error conditions. Missing templates are logged so callers can diagnose
configuration issues.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)

_TEMPLATE_DIR = (
    Path(__file__).resolve().parent
    / ".."
    / "application"
    / "prompts"
    / "templates"
    / "test_generation"
)


def _load_template(name: str) -> str:
    """Return the contents of ``name`` template or an empty string.

    Args:
        name: Base filename of the template without extension.

    Returns:
        The stripped template text. Logs a warning when the template is missing
        so callers can surface configuration problems without raising.
    """

    path = _TEMPLATE_DIR / f"{name}.md"
    try:
        return path.read_text().strip()
    except FileNotFoundError:
        logger.warning("Edge case template %s missing at %s", name, path)
        return ""


BOUNDARY_VALUES_PROMPT = _load_template("boundary_values")
"""Prompt encouraging tests that hit numeric and collection boundaries."""

ERROR_CONDITIONS_PROMPT = _load_template("error_conditions")
"""Prompt guiding generation of failure-path assertions."""


def build_edge_case_prompts() -> dict[str, str]:
    """Return available edge-case prompt templates.

    The mapping keys correspond to template names such as ``boundary_values``
    or ``error_conditions``. Templates that cannot be located are omitted from
    the result.
    """

    prompts: dict[str, str] = {}
    for key, content in {
        "boundary_values": BOUNDARY_VALUES_PROMPT,
        "error_conditions": ERROR_CONDITIONS_PROMPT,
    }.items():
        if content:
            prompts[key] = content
    return prompts


__all__ = [
    "BOUNDARY_VALUES_PROMPT",
    "ERROR_CONDITIONS_PROMPT",
    "build_edge_case_prompts",
]
