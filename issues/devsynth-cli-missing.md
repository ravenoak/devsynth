# devsynth CLI missing after setup
Milestone: 0.1.0a1
Status: closed
Priority: medium
Dependencies: scripts/install_dev.sh, poetry install --with dev --all-extras

## Problem Statement
Fresh environments lack the `devsynth` CLI entry point, producing `ModuleNotFoundError: No module named 'devsynth'` when running project commands before installation completes.

## Resolution
The `scripts/verify_post_install.py` script has been enhanced to explicitly check for the existence of the `devsynth` executable within the Poetry virtual environment's `bin` directory. If the executable is not found, `verify_post_install.py` will now exit with a specific error code. The `install_dev.sh` script's `ensure_devsynth_cli` function, which calls `verify_post_install.py`, will now correctly detect this failure and trigger a retry of `poetry install --with dev --all-extras`. This robustifies the installation process, ensuring the `devsynth` CLI is properly installed and available.

## Action Plan
- [x] Ensure `poetry install --with dev --all-extras` runs during environment provisioning.
- [x] Document this requirement in maintainer setup guides.
- [x] Add checks to `scripts/install_dev.sh` to verify the entry point exists and guide users if missing.
- [x] Update `scripts/verify_post_install.py` to explicitly check for the `devsynth` executable.

## Progress
- 2025-09-12: Encountered missing `devsynth` CLI; running `poetry install --with dev --all-extras` restored functionality.
- 2025-09-12: scripts/install_dev.sh now runs `poetry install --with dev --all-extras` and verifies the `devsynth` entry point.
- 2025-09-15: Reproduced missing CLI in fresh session; `poetry install --with dev --all-extras` restored entry point and smoke tests passed.
- 2025-09-20: New container session still reports `ModuleNotFoundError: No module named 'devsynth'` until `poetry install --with dev --all-extras` runs; captured in diagnostics/devsynth_cli_missing_20250920.log and diagnostics/poetry_install_20250920.log for follow-up.
- 2025-09-21: `poetry run devsynth --help` again failed with `ModuleNotFoundError` before reinstall; running `poetry install --with dev --all-extras` restored the CLI and extras, and a follow-up `bash scripts/install_dev.sh` captured a clean bootstrap in diagnostics/install_dev_20250921T054430Z.log.
- 2025-09-24: Modified `scripts/verify_post_install.py` to explicitly check for the `devsynth` executable, improving diagnostic and retry reliability.

## Next Actions
- [ ] Monitor for further occurrences of the `devsynth` CLI missing in fresh environments.

## References
- docs/plan.md (2025-09-12 entry)
- docs/tasks.md items 1.8 and 18.6