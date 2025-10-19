# Unify advanced test modes into `devsynth run-tests`
Milestone: 0.1.x
Status: Proposed
Priority: High
Dependencies: epics/scripts-consolidation-into-main-application.md; unified-test-cli-implementation.md

## Problem Statement
Advanced test runners (incremental/balanced/critical/prioritized/distributed) live as separate scripts (e.g., `scripts/run_unified_tests.py` and others). The CLI already provides `run-tests`, but lacks a first-class `--mode` surface that consolidates these behaviors.

## Action Plan
- Add a `--mode` option to `run-tests` supporting: `incremental`, `balanced`, `fast`, `critical`, and default behavior.
- Move minimal logic from scripts into `devsynth.testing` helpers invoked by `run-tests` (no subprocess calls to other scripts).
- Provide parity for presets (`--preset fast/recent`, prioritization toggles, process counts under xdist) with sensible defaults.
- Update docs and deprecate orchestration scripts, pointing to the single CLI.

## Acceptance Criteria
- `devsynth run-tests --mode incremental` runs only tests impacted by recent changes.
- `--mode balanced` evenly distributes test load across processes.
- `--mode fast` restricts to fast tests; `--mode critical` prioritizes high-risk tests.
- No dependency on `scripts/*` files at runtime; unit tests validate option surfaces and behavior.

## References
- `scripts/run_unified_tests.py`
- `src/devsynth/application/cli/commands/run_tests_cmd.py`
