# Expand test generation capabilities
Milestone: 0.1.0-alpha.2
Status: blocked

Priority: high
Dependencies: [LM Studio mock service for deterministic tests](archived/LM-Studio-mock-service-for-deterministic-tests.md), docs/specifications/expand-test-generation-capabilities.md, tests/behavior/features/expand_test_generation_capabilities.feature

## Problem Statement
Expand test generation capabilities is not yet implemented, limiting DevSynth's capabilities.



Automated unit test generation works but integration coverage is lacking.

- Implement integration test scaffolding for generated modules
- Improve prompt templates for edge cases
- Document recommended review workflow for generated tests

## Action Plan
- Define the detailed requirements.
- Implement the feature to satisfy the requirements.
- Create appropriate tests to validate behavior.
- Update documentation as needed.

## Progress
- 2025-02-19: LM Studio mock service completed; awaiting marker normalization.
- Tracked by [c07240c1](../commit/c07240c1).
- Expanded scenario scaffolding [ce68098d](../commit/ce68098d).
- 2025-08-19: Speed marker normalization remains unresolved; `verify_test_markers.py` reports misaligned markers in `tests/behavior/steps` (e.g., `test_agent_api_steps.py`).
- Further expansion depends on [LM Studio mock service for deterministic tests](archived/LM-Studio-mock-service-for-deterministic-tests.md).

## References
- Specification: docs/specifications/expand-test-generation-capabilities.md
- BDD Feature: tests/behavior/features/expand_test_generation_capabilities.feature

- Related: [Normalize and verify test markers](archived/Normalize-and-verify-test-markers.md)
- Related: [LM Studio mock service for deterministic tests](archived/LM-Studio-mock-service-for-deterministic-tests.md)
