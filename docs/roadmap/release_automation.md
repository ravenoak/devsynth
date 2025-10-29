---

author: DevSynth Team
date: '2025-07-07'
last_reviewed: '2025-07-10'
status: published
tags:
  - release
  - ci
  - automation
title: DevSynth Release Automation Workflow
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Roadmap</a> &gt; DevSynth Release Automation Workflow
</div>

# DevSynth Release Automation Workflow

**Note:** DevSynth is currently in a pre-release stage. Release automation steps may change until the project reaches 1.0.

This document outlines the intended continuous integration workflow for tagging and publishing DevSynth releases. It consolidates the steps described in the archived **RELEASE_PLAN_UPDATE_PLAN** document and reflects the current repository layout. For deployment-related feature status, see the [Feature Status Matrix](../implementation/feature_status_matrix.md).

## Overview

Releases are managed through GitHub Actions. The workflow is stored in `.github/workflows.disabled/release.yml`. When enabled and moved to `.github/workflows/`, it will:

1. Trigger on push of tags matching `v*.*.*`.
2. Build and publish the package to PyPI using `pypa/gh-action-pypi-publish`.
3. Build the MkDocs documentation site.
4. Deploy the site to GitHub Pages using `peaceiris/actions-gh-pages`.

The same workflow also ensures the documentation build succeeds before publication. Documentation validation is covered by a separate `validate_documentation.yml` job.

## Steps for a Release

1. Update `pyproject.toml` with the new version and commit the change.
2. Tag the commit with the release version using `git tag -s vX.Y.Z` and push the tag.
3. Once the tag is pushed, GitHub Actions runs the release workflow.
4. After the workflow completes, verify that the package appears on PyPI and the documentation site is updated.

## Repository Structure Notes

- Workflows are currently stored under `.github/workflows.disabled/`. Move them to `.github/workflows/` when ready to activate automation.
- Documentation lives in `docs/` and is built using `mkdocs`.
- Python packaging is managed with Poetry (`pyproject.toml`).

By following this process, DevSynth maintains a consistent release mechanism that automatically publishes packages and documentation whenever a signed tag is pushed.
## Implementation Status

Release automation is **planned**. The workflow remains disabled until the tasks
in [issue 103](../../issues/archived/Integration-and-performance-work.md) are complete.
