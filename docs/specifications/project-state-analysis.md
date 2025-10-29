---
author: DevSynth Team
date: 2025-08-19
last_reviewed: 2025-08-19
status: draft
tags:

- specification

title: Project State Analysis
version: 0.1.0a1
---

<!--
Required metadata fields:
- author: document author
- date: creation date
- last_reviewed: last review date
- status: draft | review | published
- tags: search keywords
- title: short descriptive name
- version: specification version
-->

# Summary

## Socratic Checklist
- What is the problem?
  Projects lack an automated way to summarize their current state and surface gaps
  between requirements, specifications, tests, and code.
- What proofs confirm the solution?
  Running project state analysis on a sample project yields artifact counts and a
  health score demonstrating successful evaluation.

## Motivation

## What proofs confirm the solution?
- BDD scenarios in [`tests/behavior/features/project_state_analysis.feature`](../../tests/behavior/features/project_state_analysis.feature) ensure termination and expected outcomes.
- Finite state transitions and bounded loops guarantee termination.


Understanding the maturity of a codebase helps teams decide next steps in the
engineering workflow. By inspecting available requirements, specifications,
tests, and code, DevSynth can guide contributors toward the most impactful
tasks.

## Specification

- Provide a function ``analyze_project_state(project_path: str)`` that returns a
  dictionary describing the project's current state.
- The result **MUST** include counts for requirements, specifications, tests,
  and code files.
- The result **MUST** include a ``health_score`` between ``0`` and ``10``.

## Acceptance Criteria
- Given a project containing requirements, specifications, tests, and code
  files,
  When ``analyze_project_state`` is executed,
  Then the returned counts for each artifact type are greater than zero,
  And the ``health_score`` is between ``0`` and ``10``.
