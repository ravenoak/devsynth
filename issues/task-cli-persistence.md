# task CLI persistence
Milestone: 0.1.0a1
Status: closed
Priority: low
Dependencies: scripts/install_dev.sh

## Problem Statement
The `go-task` binary installed by `scripts/install_dev.sh` is not persistent across
fresh environments or container sessions, requiring manual reinstallation.

## Action Plan
- [x] Investigate caching strategies (e.g., persisting `$HOME/.local/bin`).
- [x] Consider automatic installation during project bootstrap.
- [x] Document the chosen approach in maintainer guides.

## References
- docs/tasks.md item 15.2
- docs/plan.md Notes section (2025-10-07 entry)
## Progress
- 2025-09-12: Fresh environment lacked `task`; ran `bash scripts/install_dev.sh` to install version 3.44.1. Persistence strategy still required.
- 2025-09-12: scripts/install_dev.sh now installs go-task into `$HOME/.local/bin` and verifies availability on each run.
