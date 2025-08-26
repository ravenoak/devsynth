---
title: "Post‑release Validation Checklist"
date: "2025-08-26"
version: "0.1.0a1"
status: "living"
author: "DevSynth Team"
last_reviewed: "2025-08-26"
---

# Post‑release Validation Checklist

Perform these steps after publishing a tag and artifacts to ensure the release is usable by end users.

## Environment setup
- Use a clean Python 3.12 virtual environment (venv or pipx).
- Avoid reusing the development environment.

## Install and verify
- Install from PyPI or TestPyPI (depending on workflow):
  - `pip install devsynth==<version>`
  - or `pip install --extra-index-url https://test.pypi.org/simple devsynth==<version>`
- Verify CLI basics:
  - `devsynth --help`
  - `devsynth doctor`
- Optional: if testing from a repo checkout, run the fast smoke tests subset:
  - `poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1`

## Sanity checks
- Confirm version displayed in CLI matches the tag.
- Confirm provider defaults: DEVSYNTH_PROVIDER=stub, DEVSYNTH_OFFLINE=true in test CLI context (see docs/guidelines and tests).
- Ensure no unexpected network activity occurs by default.

## Artifacts and docs
- Attach or link HTML test reports produced during CI.
- Ensure CHANGELOG.md and docs/release/0.1.0-alpha.1.md reflect the published version and artifacts.

## Report
- Record findings and any issues under docs/release/0.1.0-alpha.1.md.
- If problems are found, open a ticket and link it from the release notes; add to docs/testing/known_flakes.md if applicable.
