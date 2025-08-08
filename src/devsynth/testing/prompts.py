"""Prompt templates for DevSynth testing utilities.

This module contains prompt strings used by the testing helpers to
bootstrap integration test generation.
"""

INTEGRATION_TEST_PROMPT = (
    "You are an expert software tester. Given a description of a module, "
    "write pytest integration tests that exercise realistic workflows. "
    "Ensure each test contains meaningful assertions and covers edge cases "
    "without using placeholders like 'assert True'."
)

__all__ = ["INTEGRATION_TEST_PROMPT"]
