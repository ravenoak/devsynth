# task CLI missing
Milestone: 0.1.0a1
Status: closed
Priority: medium
Dependencies: scripts/install_dev.sh

## Problem Statement
`task --version` returns `command not found` after running `poetry install --with dev --all-extras`. The go-task binary may not be installed or `$PATH` is missing `$HOME/.local/bin`.

## Action Plan
- [x] Verify `scripts/install_dev.sh` installs go-task to `$HOME/.local/bin`.
- [x] Ensure `$HOME/.local/bin` is on the PATH in development environments.
- [x] Document the requirement in maintainer setup instructions.

## Progress
- 2025-09-30: Detected absence of `task` CLI during environment validation.
- 2025-10-01: `task --version` still reports command not found after `poetry install`.
- 2025-10-02: Installed go-task via `bash scripts/install_dev.sh`; `task --version` returns 3.44.1 and PATH includes `$HOME/.local/bin`. Maintainer docs updated.

## References
- docs/plan.md section on environment baseline
