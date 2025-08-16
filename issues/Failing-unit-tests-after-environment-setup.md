# Issue 120: Failing unit tests after environment setup

Milestone: 0.1.0-alpha.1
Status: open
Priority: high
Dependencies: None


Running `deployment/bootstrap_env.sh` followed by
`poetry run pytest -m "not memory_intensive"` results in multiple
failing tests, particularly in the code analysis pipeline.

## Steps to reproduce
1. Execute `deployment/bootstrap_env.sh`.
2. Run `poetry run pytest -m "not memory_intensive"`.

## Progress
- `deployment/bootstrap_env.sh` completed without errors.
- `devsynth run-tests --speed=fast` reports two failures in `tests/unit/general/test_provider_logging.py` due to missing `lmstudio`.
- `tests/behavior/test_simple_standalone.py` raises `FileNotFoundError` for required sample files.
- Previous runs also reported failures in `test_repo_analyzer` and `test_transformer`.
- `pip check` confirms no broken requirements.
- Latest `devsynth run-tests --speed=fast` run produced five errors, including a failure in `tests/behavior/requirements_wizard/test_logging_and_priority_steps.py`.
- Current fast test run reports a single failure in `tests/unit/interface/test_nicegui_bridge.py::test_session_storage_roundtrip` due to missing session initialization.
- After running the environment provisioning script, `devsynth run-tests --speed=fast` still fails: `tests/unit/interface/test_nicegui_bridge.py::test_session_storage_roundtrip` raises `RuntimeError: app.storage.user can only be used with page builder functions`.

## References

- None
