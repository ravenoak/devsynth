# Issue 125: Dialectical audit reports undocumented features

Milestone: 0.1.0-alpha.1

The latest dialectical audit found numerous features referenced in tests or documentation without corresponding documentation or code. See `dialectical_audit.log` for the full list of open questions.

## Steps to reproduce
1. Run `poetry run python scripts/dialectical_audit.py`.
2. Inspect `dialectical_audit.log` for the reported inconsistencies.

## Suggested improvement
Review each question in the audit log and update documentation, tests, or code accordingly. Split this issue if needed to track individual features.

## Progress
- Pending review of audit log entries
- Dialectical audit tooling added in [f505a68f](../commit/f505a68f).
- Status: open
