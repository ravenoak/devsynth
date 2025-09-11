# task CLI missing
Milestone: 0.1.0a1
Status: open
Priority: medium
Dependencies: scripts/install_dev.sh

## Problem Statement
`task --version` returns `command not found` after running `poetry install --with dev --all-extras`. The go-task binary may not be installed or `$PATH` is missing `$HOME/.local/bin`.

## Action Plan
- [ ] Verify `scripts/install_dev.sh` installs go-task to `$HOME/.local/bin`.
- [ ] Ensure `$HOME/.local/bin` is on the PATH in development environments.
- [ ] Document the requirement in maintainer setup instructions.

## Progress
- 2025-09-30: Detected absence of `task` CLI during environment validation.
- 2025-10-01: `task --version` still reports command not found after `poetry install`.

## References
- docs/plan.md section on environment baseline
