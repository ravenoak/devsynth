# Issue 114: Requirements wizard failures
Milestone: 0.1.0-alpha.1

Behaviour and integration tests for the requirements wizard (`tests/integration/general/test_requirements_gathering.py` and related behaviour step files) fail due to logging errors and incorrect persistence of the priority value. Update `DevSynthLogger` to handle `exc_info` correctly and verify the gather and wizard flows write expected configuration.

## Progress
- Updated logging to handle `exc_info` correctly and ensured priority persistence.
- `tests/integration/general/test_requirements_gathering.py` passes.
- Fix implemented in [2452a3f5](../commit/2452a3f5).
- Status: closed
