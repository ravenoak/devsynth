# devsynth CLI missing after setup
Milestone: 0.1.0a1
Status: open
Priority: medium
Dependencies: scripts/install_dev.sh, poetry install --with dev --all-extras

## Problem Statement
Fresh environments lack the `devsynth` CLI entry point, producing `ModuleNotFoundError: No module named 'devsynth'` when running project commands before installation completes.

## Action Plan
- [ ] Ensure `poetry install --with dev --all-extras` runs during environment provisioning.
- [ ] Document this requirement in maintainer setup guides.
- [ ] Add checks to `scripts/install_dev.sh` to verify the entry point exists and guide users if missing.

## Progress
- 2025-09-12: Encountered missing `devsynth` CLI; running `poetry install --with dev --all-extras` restored functionality.

## References
- docs/plan.md (2025-09-12 entry)
- docs/tasks.md items 1.8 and 18.6
