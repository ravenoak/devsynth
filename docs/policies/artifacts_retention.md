---
title: "Artifacts, Logs, and Cache Retention Policy"
author: "DevSynth Team"
date: "2025-08-25"
status: "published"
version: "0.1.0a1"
tags:
  - policy
  - retention
  - hygiene
last_reviewed: "2025-08-25"
---

# Artifacts, Logs, and Cache Retention Policy {#artifacts-retention}

This policy defines retention and cleanup practices for build/test artifacts, caches, and logs. It supports reproducibility and clean CI by preventing workspace bloat and ensuring deterministic reruns.

## Scope
- Test reports: `test_reports/`
- Coverage: `.coverage`, `coverage.xml`, `htmlcov/`
- Pytest caches: `.pytest_cache/`
- Build artifacts: `build/`, `dist/`
- Transient logs: files under `logs/` (if present) not committed to VCS

## Defaults
- Local development: retain latest run artifacts; clean on demand via `scripts/clean_artifacts.py`.
- CI: workflows should remove artifacts not uploaded as build artifacts.
- Never delete files tracked by Git.

## Cleanup Procedure
Use the provided script:

```
poetry run python scripts/clean_artifacts.py --dry-run   # default; shows what would be removed
poetry run python scripts/clean_artifacts.py --yes       # actually remove
```

Optional flags:
- `--keep-reports` to keep `test_reports/`
- `--keep-coverage` to keep coverage outputs (`.coverage`, `coverage.xml`, `htmlcov/`)

## Safety and Determinism
- The script only removes known artifact paths and ignores Git-tracked files.
- Paths outside the repository root are never touched.
- CI uses explicit paths; local runs default to `--dry-run` for safety.

## Traceability
- ReqID: HYGIENE-RET-01 — Provide safe cleanup routine.
- ReqID: HYGIENE-RET-02 — Document retention policy and defaults.

## References
- `project guidelines` (repo hygiene, isolation)
- `docs/plan.md` (determinism)
- `.github/workflows/*` (artifact upload steps)
