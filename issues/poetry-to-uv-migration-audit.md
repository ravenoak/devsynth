# Poetry-to-uv Migration: Audit Current Configuration
Milestone: 0.2.0-alpha.1
Status: planning
Priority: high
Dependencies: issues/poetry-to-uv-migration-epic.md

## Problem Statement
Before migrating to uv, we need a comprehensive understanding of how Poetry is currently used across the DevSynth codebase, including all dependencies, scripts, workflows, and configurations.

## Action Plan
- Catalog all Poetry-specific files and configurations
- Document dependency structure and optional extras
- Map Poetry command usage across scripts and workflows
- Identify custom Poetry configurations and scripts
- Create inventory of Poetry environment assumptions

## Acceptance Criteria
- Complete inventory of all Poetry references in codebase (should find ~400+ occurrences)
- Documentation of all dependencies with versions and extras
- List of all scripts using Poetry commands
- Identification of Poetry-specific features in use
- Risk assessment for each Poetry usage pattern

## Progress
- 2025-10-28: Task created

## References
- pyproject.toml: Hybrid Poetry/PEP 621 configuration
- poetry.lock: Current lockfile with 2.2.1 format
- scripts/: Core setup and maintenance scripts
- .github/workflows/: CI/CD pipeline files
- Taskfile.yml: Build and development automation
