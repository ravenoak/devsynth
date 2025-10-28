# Poetry-to-uv Migration: Migrate Scripts and Configurations
Milestone: 0.2.0-alpha.1
Status: planning
Priority: high
Dependencies: issues/poetry-to-uv-migration-parallel-env.md

## Problem Statement
Core development scripts (install_dev.sh, codex_setup.sh, codex_maintenance.sh) and configurations need to be updated to use uv instead of Poetry.

## Action Plan
- Rewrite scripts/install_dev.sh for uv
- Update scripts/codex_setup.sh and codex_maintenance.sh
- Convert Poetry environment management to uv equivalents
- Update Taskfile.yml commands from poetry run to uv run
- Test script execution in parallel uv environment

## Acceptance Criteria
- install_dev.sh works with uv (installs uv, creates environment, runs validation)
- codex_setup.sh and codex_maintenance.sh use uv commands
- Taskfile.yml commands converted and functional
- Environment setup completes successfully
- All script validations pass

## Progress
- 2025-10-28: Task created

## References
- scripts/install_dev.sh: ~400 lines of Poetry-centric setup
- scripts/codex_setup.sh: CI environment provisioning
- scripts/codex_maintenance.sh: Environment maintenance
- Taskfile.yml: ~200 Poetry commands across ~500 lines
