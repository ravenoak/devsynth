# Poetry-to-uv Migration: Migrate GitHub Workflows
Milestone: 0.2.0-alpha.1
Status: planning
Priority: high
Dependencies: issues/poetry-to-uv-migration-scripts-migration.md

## Problem Statement
30+ GitHub workflow files need to be updated from Poetry to uv, including caching strategies, dependency installation, and environment setup.

## Action Plan
- Update CI workflow actions from abatilo/actions-poetry to uv setup
- Convert dependency installation steps
- Update caching configuration for uv
- Test workflow execution in feature branch
- Validate CI performance improvements

## Acceptance Criteria
- All workflow files updated to use uv
- Dependency installation steps converted
- Caching works correctly with uv cache structure
- Workflows pass in feature branch testing
- Performance benchmarks show expected 3x speedup

## Progress
- 2025-10-28: Task created

## References
- .github/workflows/ci.yml: Main CI pipeline
- .github/workflows/ci_fast_and_smoke.yml: Fast CI variant
- 30+ workflow files total in .github/workflows/
- Current Poetry action: abatilo/actions-poetry@v3
