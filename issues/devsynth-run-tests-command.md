# devsynth run-tests command
Milestone: 0.1.0-alpha.2
Status: in progress
Priority: high
Dependencies: docs/specifications/devsynth-run-tests-command.md, tests/behavior/features/devsynth_run_tests_command.feature

## Problem Statement
devsynth run-tests command is not yet implemented, limiting DevSynth's capabilities.


## Action Plan
- Review `docs/specifications/devsynth-run-tests-command.md` for requirements.
- Implement the feature to satisfy the requirements.
- Add or update BDD tests in `tests/behavior/features/devsynth_run_tests_command.feature`.
- Update documentation as needed.

## Progress
- 2025-02-19: extracted from dialectical audit backlog.
- 2025-08-21: After activating the virtualenv, running `poetry run devsynth run-tests --speed=fast` emitted an `LMStudioProvider` missing warning and stalled, indicating the command and optional dependency handling remain incomplete.
- 2025-08-21: consolidated duplicate [Run tests from the CLI](archived/run-tests-from-the-cli.md) ticket.

## References
- Specification: docs/specifications/devsynth-run-tests-command.md
- BDD Feature: tests/behavior/features/devsynth_run_tests_command.feature
