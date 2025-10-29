---
last_reviewed: "2025-08-11"
status: draft
tags:
  - testing
  - workflow
  - automation
title: Test Generation Review Workflow
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; Test Generation Review Workflow
</div>

# Test Generation Review Workflow

## Overview

This guide describes how automatically generated tests should be reviewed and incorporated into the codebase.

## Workflow

1. **Generate tests** – run the test agent or related tooling to create initial tests.
2. **Scaffold integration tests** – use `devsynth.testing.generation.scaffold_integration_tests`
   to create placeholder files when coverage is missing.
3. **Manual refinement** – examine generated tests for correctness, add coverage for
   edge cases (invalid inputs, async flows, and error conditions), and replace any
   assertions used as placeholders with skipped scaffolds.
4. **Lint and run tests** – execute `poetry run pre-commit run --files` on changed files
   and `poetry run pytest` to verify behavior.
5. **Peer review** – open a pull request and follow cross-functional review guidelines.

## Review Workflow

1. **Open a pull request** containing the generated or updated tests.
2. **Inspect scaffolds** – ensure placeholder integration tests created with
   `devsynth.testing.generation` use `pytest.mark.skip` and do not fail the
   suite.
3. **Validate edge cases** – confirm boundary value and error condition
   templates have been applied where appropriate.
4. **Run checks** – verify `poetry run pre-commit run --files` and the test
   suite pass before approval.
5. **Finalize** – address reviewer feedback and merge once all checklist items
   are satisfied.

## Review Checklist

Before merging generated tests, ensure reviewers verify the following:

- **Meaningful coverage** – tests exercise realistic workflows and edge cases.
- **No placeholders** – templates or skipped examples have been replaced with real assertions.
- **Style compliance** – code follows project linting and naming conventions.
- **Integration templates referenced** – new modules leverage templates from
  `tests/integration/templates/` when scaffolding tests.

- **Edge case prompts** – when necessary, developers use prompt templates in
  `templates/test_generation/` to generate tests for boundary values and error
  conditions.
- **Skipped scaffolds** – unfinished integration tests are marked with
  `pytest.mark.skip` rather than failing assertions.

## Edge Case Templates

Edge case prompt templates live in `templates/test_generation/`. Use these templates to guide the agent when generating tests for boundary values and error conditions.
