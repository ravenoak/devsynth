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
- 2025-08-21: Enabled Poetry virtual environment with `poetry config virtualenvs.create true` and reinstalled dependencies; `poetry env info --path` now reports `/root/.cache/pypoetry/virtualenvs/devsynth-MeXVnKii-py3.12`.
- 2025-08-28: Updated `scripts/install_dev.sh` to validate `poetry env info --path` and `task --version`, ensuring early detection of misconfigured environments.

## References
- docs/release/0.1.0-alpha.1.md
