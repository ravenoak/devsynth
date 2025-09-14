"""Prompt templates for DevSynth testing utilities.

This module contains prompt strings used by the testing helpers to
bootstrap integration test generation.
"""

INTEGRATION_TEST_PROMPT: str = (
    "You are an expert software tester. Given a description of a module, "
    "write pytest integration tests that exercise realistic workflows and "
    "boundary conditions. Cover invalid inputs, error-handling paths, and "
    "concurrency or asynchronous behavior where applicable. Account for "
    "edge cases such as empty or malformed payloads, extreme values, missing "
    "permissions, network or filesystem failures, and cleanup of external "
    "resources. Use fixtures and parameterization to reduce duplication. "
    "Ensure each test contains meaningful assertions, applies 'pytest.mark.asyncio' "
    "for async code, avoids placeholders like 'assert True' or 'pass', and never "
    "performs real network calls."
)

__all__: list[str] = ["INTEGRATION_TEST_PROMPT"]
