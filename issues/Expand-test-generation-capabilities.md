# Expand test generation capabilities
Milestone: 0.2.0
Status: blocked

Priority: medium
Dependencies: [Normalize and verify test markers](Normalize-and-verify-test-markers.md), [LM Studio mock service for deterministic tests](archived/LM-Studio-mock-service-for-deterministic-tests.md)


Automated unit test generation works but integration coverage is lacking.

- Implement integration test scaffolding for generated modules
- Improve prompt templates for edge cases
- Document recommended review workflow for generated tests

## Progress
- 2025-02-19: LM Studio mock service completed; awaiting marker normalization.
- Tracked by [c07240c1](../commit/c07240c1).
- Expanded scenario scaffolding [ce68098d](../commit/ce68098d).
- Further expansion depends on [Normalize and verify test markers](Normalize-and-verify-test-markers.md) and [LM Studio mock service for deterministic tests](archived/LM-Studio-mock-service-for-deterministic-tests.md).

## References

- Related: [Normalize and verify test markers](Normalize-and-verify-test-markers.md)
- Related: [LM Studio mock service for deterministic tests](archived/LM-Studio-mock-service-for-deterministic-tests.md)
