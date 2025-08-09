"""Prompt templates for DevSynth testing utilities.

This module contains prompt strings used by the testing helpers to
bootstrap integration test generation.
"""

INTEGRATION_TEST_PROMPT = (
    "You are an expert software tester. Given a description of a module, "
    "write pytest integration tests that exercise realistic workflows and boundary conditions. "
    "Cover invalid inputs, error-handling paths, and concurrency or asynchronous behavior where applicable. "
    "Use fixtures and parameterization to reduce duplication. "
    "Ensure each test contains meaningful assertions, applies 'pytest.mark.asyncio' for async code, "
    "and avoids placeholders like 'assert True' or 'pass'."
)

__all__ = ["INTEGRATION_TEST_PROMPT"]
