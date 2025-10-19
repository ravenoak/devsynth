# Add `devsynth traceability` command group
Milestone: 0.1.x
Status: Proposed
Priority: Medium
Dependencies: epics/scripts-consolidation-into-main-application.md

## Problem Statement
Traceability checks are spread across scripts: `verify_requirements_traceability.py`, `verify_reqid_references.py`, `verify_docstring_reqids.py`. Users should be able to run these via a unified CLI group with consistent output and artifacts.

## Action Plan
- Create `traceability` group with subcommands:
  - `requirements-matrix`
  - `reqid-references`
  - `docstring-reqids`
- Provide machine-readable outputs in `diagnostics/` or `test_reports/`.
- Write unit tests for each subcommand's core logic.
- Deprecate scripts with wrapper messages pointing to CLI.

## Acceptance Criteria
- `devsynth traceability <subcmd>` exists and returns non-zero on violations.
- Artifacts are written and referenced in console output.
- Documentation updated; scripts flagged for deprecation.

## References
- `scripts/verify_requirements_traceability.py`
- `scripts/verify_reqid_references.py`
- `scripts/verify_docstring_reqids.py`
