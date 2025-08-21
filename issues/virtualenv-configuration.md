# Virtualenv configuration enforcement
Milestone: 0.1.0
Status: open
Priority: medium
Dependencies: docs/release/0.1.0-alpha.1.md

## Problem Statement
Developers run commands in the global Python environment because `poetry` is configured with `virtualenvs.create=false`. This leads to inconsistent dependency resolution and missing console scripts such as `devsynth`.

## Action Plan
- Document the requirement to enable Poetry-managed virtual environments.
- Update setup scripts to enforce `poetry config virtualenvs.create true`.
- Verify `poetry env info --path` in CI to ensure the virtual environment is active.

## Progress
- 2025-08-20: Identified missing virtualenv after failing to run `devsynth` tests.
- 2025-08-20: `poetry env info --path` produced no output even after `poetry install`, confirming virtualenv remains disabled.

## References
- docs/release/0.1.0-alpha.1.md
