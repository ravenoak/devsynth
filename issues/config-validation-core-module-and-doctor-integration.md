# Refactor config validation into core module and integrate with `doctor`
Milestone: 0.1.x
Status: Proposed
Priority: High
Dependencies: epics/scripts-consolidation-into-main-application.md

## Problem Statement
`doctor_cmd` dynamically imports `scripts/validate_config.py` to perform schema and env validation. This creates an undesirable coupling to ad-hoc script code and complicates testing and reuse.

## Action Plan
- Create `src/devsynth/application/config_validation.py` exposing:
  - `load_config(path: Path) -> dict`
  - `validate_config(config: dict) -> list[str]`
  - `validate_environment_variables(config: dict) -> list[str]`
  - `check_config_consistency(configs: dict[str, dict]) -> list[str]`
- Update `doctor_cmd` to import these functions directly; remove dynamic script import.
- Add unit tests for validation utilities and `doctor_cmd` integration.
- Mark `scripts/validate_config.py` as deprecated; update docs to reference `devsynth doctor`.

## Acceptance Criteria
- `doctor_cmd` no longer imports from `scripts/validate_config.py` at runtime.
- New module covered by tests (≥90% coverage for functions above).
- `devsynth doctor` reports the same or better diagnostics as before.
- Documentation updated; script marked deprecated with migration guidance.

## References
- `src/devsynth/application/cli/commands/doctor_cmd.py`
- `scripts/validate_config.py`
