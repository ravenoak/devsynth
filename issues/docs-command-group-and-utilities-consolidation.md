# Create `devsynth docs` command group and consolidate utilities
Milestone: 0.1.x
Status: Proposed
Priority: Medium
Dependencies: epics/scripts-consolidation-into-main-application.md; validate-metadata-command.md

## Problem Statement
Documentation utilities (internal link validation, index generation, breadcrumb dedupe, metadata validation) exist as scripts. We already have `validate-metadata` in CLI; the rest should be accessible under a consistent `devsynth docs` command group.

## Action Plan
- Add a `docs` group with subcommands:
  - `validate-internal-links`
  - `generate-index`
  - `dedupe-breadcrumbs`
  - `validate-metadata` (reuse existing command)
- Migrate logic from scripts into reusable library helpers with tests.
- Provide consistent exit codes and summary output for CI consumption.
- Mark the overlapping scripts as deprecated wrappers.

## Acceptance Criteria
- `devsynth docs <subcommand>` exists and passes unit tests.
- Overlapping scripts emit deprecation warnings and point to CLI equivalents.
- Documentation updated (developer guides and tasks).

## References
- `scripts/validate_internal_links.py`, `scripts/generate_doc_index.py`, `scripts/deduplicate_breadcrumbs.py`
- `src/devsynth/application/cli/commands/validate_metadata_cmd.py`
