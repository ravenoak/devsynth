# Fix failing test tests/behavior/steps/test_code_generation_steps.py::tests_passed

Milestone: 0.1.0-alpha.1
Status: open

Priority: high
Dependencies: [tests/behavior/steps/test_code_generation_steps.py](../tests/behavior/steps/test_code_generation_steps.py)


The test `tests/behavior/steps/test_code_generation_steps.py::tests_passed` fails with `AttributeError: 'NoneType' object has no attribute 'execute_command'`. Investigate and resolve the failure.

## Steps to Reproduce
1. Run `poetry run pytest tests/behavior/steps/test_code_generation_steps.py::tests_passed`

## Progress
- Test re-run still fails with `AttributeError: 'NoneType' object has no attribute 'execute_command'`.
- Running the environment provisioning script followed by the same test run continues to raise the `AttributeError` with `mock_manager` being `None`.

## References

- None
