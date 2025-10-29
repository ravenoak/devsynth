---
author: DevSynth Team
date: "2025-08-25"
status: living-doc
version: "0.1.0a1"
---
# Documentation Consolidation Plan (Single Sources of Truth)

Purpose: Reduce duplication and drift by declaring canonical locations per topic and linking/retiring overlapping docs. Aligned with project guidelines and docs/plan.md.

## Canonical Mapping
- Testing (strategy, fixtures, speeds, running): docs/developer_guides/testing.md
  - Cross-links from: README.md (Running Tests), docs/testing/*, tests/README.md, scripts/README.md
  - Remove/retire conflicting snippets elsewhere; prefer a short pointer.
- CLI commands (all commands, options, run-tests behavior): docs/user_guides/cli_command_reference.md
  - Cross-links from: README.md (CLI Reference), testing guide (run-tests section)
- Quickstart and Installation: docs/getting_started/quick_start_guide.md and docs/getting_started/installation.md
  - Cross-links from: README.md (concise pointers only)
- Run-tests workflow rationale, segmentation and caching TTL: docs/developer_guides/testing.md (runner specifics section)
  - Mention: default marker filter (not memory_intensive) and 1h collection cache TTL with optional env override.
- Flaky tests patterns and mitigations: docs/testing/flaky_tests.md
  - Cross-links from: testing guide troubleshooting section.
- Architecture overviews: docs/architecture/overview.md
  - Cross-links from: README.md and user guides as needed.

## Actions and Status
- Create consolidation mapping doc (this file). Status: completed 2025-08-25.
- Update README.md to reference CLI Command Reference and add troubleshooting pointers. Status: completed 2025-08-25.
- Ensure testing guidance points to docs/developer_guides/testing.md and remove conflicting instructions in scattered docs over time. Status: ongoing.
- MkDocs nav to reflect canonical docs and remove dead links. Status: pending.

## Deprecations/Redirects
- Replace references to docs/user_guides/cli_reference.md with docs/user_guides/cli_command_reference.md.
- Prefer Poetry-invoked commands in all examples (poetry run ...) except advanced sections.

## Traceability
- Related tasks: docs/tasks.md items 31, 33, 35, 45.
- Plan alignment: docs/plan.md (Documentation pointers, determinism guidance).
