---
author: DevSynth Team
date: 2025-08-19
last_reviewed: 2025-08-19
status: draft
tags:

- specification

title: Review and Reprioritize Open Issues
version: 0.1.0a1
---

# Summary
Automates adjustment of ticket priorities to reflect roadmap phases.

## Socratic Checklist
- What is the problem? Priorities in `issues/` drift from the roadmap over time.
- What proofs confirm the solution? Running `devsynth reprioritize-issues` updates priorities based on milestones and reports counts.

## Motivation

## What proofs confirm the solution?
- BDD scenarios in [`tests/behavior/features/reprioritize_open_issues.feature`](../../tests/behavior/features/reprioritize_open_issues.feature) ensure termination and expected outcomes.
- Finite state transitions and bounded loops guarantee termination.

Maintainers need a repeatable way to keep the repository issue tracker aligned with current milestones without manual review.

## Specification
- Scan markdown files in `issues/` excluding `README.md` and `TEMPLATE.md`.
- For each issue, read `Milestone` and `Priority` fields.
- Set priority according to milestone mapping:
  - `Phase 1` → `high`
  - `Phase 2` → `medium`
  - any other milestone → `low`
- Provide CLI command `devsynth reprioritize-issues` that applies this mapping and prints counts for each priority.

## Acceptance Criteria
- Given an issue with milestone `Phase 1` and priority `low`, when the command runs, the issue priority becomes `high`.
- Given an issue with milestone `Phase 2` and priority `low`, when the command runs, the issue priority becomes `medium`.
- Given an issue with a different milestone, when the command runs, the issue priority becomes `low`.
- The command prints counts for `High`, `Medium`, and `Low` priorities after updates.

## References
- [Issue: Review and Reprioritize Open Issues](../../issues/reprioritize-open-issues.md)
- [BDD: reprioritize_open_issues.feature](../../tests/behavior/features/reprioritize_open_issues.feature)
