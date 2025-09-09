---
title: "Release Playbook"
date: "2025-08-26"
version: "0.1.0a1"
status: "living"
author: "DevSynth Team"
last_reviewed: "2025-08-26"
---

# DevSynth Release Playbook

This concise playbook describes the end-to-end process for preparing, validating, and publishing a DevSynth release. It aligns with project guidelines and docs/plan.md and traces to tasks in docs/tasks.md (70, 73, 75, 76, 77, 78).

## 1) Version bump and changelog
- Ensure pyproject.toml reflects the target version (PEP 440). Example: `0.1.0a1`.
- Update CHANGELOG.md with a dated section for the version (Keep a Changelog format).
- Ensure README badges and references are consistent with the version.
- Commit as a standalone PR labeled `release: version bump`.

## 2) Readiness gates (pre‑tag)
- Tests: Gate on fast + medium passing in PRs; full suite incl. slow required before tagging or on a pre‑release branch.
- Docs: mkdocs build must be green (no broken links, anchors, or fences).
- Lint/security: mypy, black --check, isort --check-only, flake8, bandit, safety must pass.
- Marker discipline: `scripts/verify_test_markers.py --report` should show zero violations.
- Artifacts: HTML report under `test_reports/` should generate via `--report`.

See: docs/release/release_readiness.md

## 3) Dry‑run workflows (on main)
- Trigger `.github/workflows/release_prep_dry_run.yml` (or wait for its scheduled run) to validate the pipeline without publishing.
- Confirm caching, environment matrix, and artifact uploads succeed.
- Required secrets (document in repo settings if private):
  - PYPI_TOKEN (TestPyPI for dry‑run when applicable)
  - GITHUB_TOKEN (provided by Actions)
  - OPTIONAL: SIGNING_KEY / PASSPHRASE if artifact signing is enabled

See: .github/workflows/release_prep_dry_run.yml

## 4) Tagging and publish workflows
- Tag format: `v<version>` (e.g., `v0.1.0a1`).
- Ensure `.github/workflows/release_prep.yml` is configured to trigger on tags matching the pattern.
- On tag push:
  - Build sdist and wheel (poetry).
  - Optionally sign artifacts.
  - Publish to TestPyPI (dry run) and/or PyPI depending on workflow configuration.
  - Upload build logs and reports as artifacts.

See: .github/workflows/release_prep.yml

## 5) Packaging sanity
- Verify metadata:
  - Classifier: `Development Status :: 3 - Alpha` present.
  - LICENSE included in sdist/wheel.
  - Tests excluded from wheel (package path is `src/devsynth`).
  - Required templates and runtime data (if any) included via package data config.
- Local check:
  - `poetry build`
  - Inspect `dist/*.whl` and `dist/*.tar.gz` contents.

## 6) Post‑release validation
- In a clean venv (Python 3.12):
  - `pip install devsynth==<version>` or `pip install --extra-index-url https://test.pypi.org/simple devsynth==<version>` if using TestPyPI.
  - Run `poetry run devsynth doctor` (when installed via Poetry) or `devsynth --help` via pipx/global install.
  - Execute fast smoke tests subset if the repo is checked out.
- Record findings in the release notes and update release status.

See: docs/release/post_release_validation.md

## 7) Documentation updates
- Cross-link this playbook from README and mkdocs nav under a new "Release" section.
- Keep docs/release/0.1.0-alpha.1.md updated with status and artifacts.
- Update docs/roadmap/release_plan.md if scope or exit criteria change.

## 8) Troubleshooting
- If fast path hangs: `poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1`.
- If markers fail: `poetry run python scripts/verify_test_markers.py --report`.
- If docs fail: `poetry run mkdocs build` and fix broken links.

## References
- project guidelines
- docs/plan.md
- docs/release/release_readiness.md
- docs/release/post_release_validation.md
- .github/workflows/release_prep*.yml
- CHANGELOG.md
