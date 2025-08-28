---
author: DevSynth Team
date: "2025-08-26"
last_reviewed: "2025-08-26"
status: published
title: DevSynth Doctor Checklist
version: "0.1.0a1"
---

# DevSynth Doctor Checklist

Purpose: a fast, deterministic diagnostic flow to validate your environment and surface common issues. Use this before filing issues or when a CI job fails locally.

Principles:
- Poetry-first execution to ensure plugins and extras are available.
- Offline-first and resource-gated by default.
- Keep runs hermetic: disable third-party plugins when triaging.

## Quick sanity

- Verify test collection works:
  - poetry run pytest --collect-only -q
- Run the built-in doctor:
  - poetry run devsynth doctor
- Fast smoke path (stable, minimal surface):
  - poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1

## Environment and installation

- Ensure Python 3.12.x and Poetry installed.
- Recommended installs (pick one):
  - Minimal dev: poetry install --with dev --extras minimal
  - Tests baseline: poetry install --with dev --extras "tests retrieval chromadb api"
  - Full maintainer: poetry install --with dev,docs --all-extras
- If imports fail during tests, re-run: poetry install

## Offline-first defaults (tests)

- By default, tests run offline with a stub provider:
  - DEVSYNTH_OFFLINE=true
  - DEVSYNTH_PROVIDER=stub
  - DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=false
- To opt into a backend locally (example: TinyDB):
  - poetry install --with dev --extras memory
  - export DEVSYNTH_RESOURCE_TINYDB_AVAILABLE=true
  - poetry run devsynth run-tests --speed=fast
- See also: docs/developer_guides/resources_matrix.md

## Marker discipline and inventory

- Validate exactly-one speed marker per test:
  - poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json
- Produce inventory for planning:
  - poetry run devsynth run-tests --inventory  # writes test_reports/test_inventory.json

## Segmentation and timeouts

- For medium/slow suites, prefer segmentation:
  - Default: --segment --segment-size 50 (tune 25–100)
- In smoke mode, a tighter default timeout applies via DEVSYNTH_TEST_TIMEOUT_SECONDS.
- Keep --no-parallel during flake triage; re-enable once stable.

## Common pitfalls

- Third-party pytest plugins causing hangs:
  - Use --smoke to set PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 and disable xdist/cov.
- Missing extras for tests:
  - Install the tests baseline extras listed above.
- Network calls during tests:
  - Ensure DEVSYNTH_OFFLINE=true and resource flags remain false unless explicitly testing integrations.

## References

- .junie/guidelines.md
- docs/developer_guides/testing.md
- docs/user_guides/cli_command_reference.md (run-tests)
- docs/developer_guides/resources_matrix.md
