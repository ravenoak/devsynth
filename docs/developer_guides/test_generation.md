---
last_reviewed: "2025-08-17"
status: draft
tags:
  - testing
  - workflow
  - automation
title: Test Generation Review Workflow
version: "0.1.0-alpha.1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; Test Generation Review Workflow
</div>

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
3. **Manual review** – examine generated tests for correctness and completeness.
4. **Replace placeholders** – implement real assertions and remove `assert False` markers.
5. **Lint and run tests** – execute `poetry run pre-commit run --files` on changed files
   and `poetry run pytest` to verify behavior.
6. **Submit for review** – open a pull request and follow cross-functional review guidelines.

## Review Checklist

Before merging generated tests, ensure reviewers verify the following:

- **Meaningful coverage** – tests exercise realistic workflows and edge cases.
- **No placeholders** – templates or skipped examples have been replaced with real assertions.
- **Style compliance** – code follows project linting and naming conventions.
- **Integration templates referenced** – new modules leverage templates from
  `tests/integration/templates/` when scaffolding tests.

## Edge Case Templates

Edge case prompt templates live in `templates/test_generation/`. Use these templates to guide the agent when generating tests for boundary values and error conditions.
