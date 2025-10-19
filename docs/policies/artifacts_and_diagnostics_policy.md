Artifacts and Diagnostics Policy

Scope
- Defines structure, naming, and retention for `artifacts/` and `diagnostics/`.

Artifacts (`artifacts/`)
- For release-grade, reproducible evidence and curated research artefacts.
- Layout: `releases/<version>/<profile>/<timestamp>/` with manifests and checksums; optional HTML coverage for releases.
- Research artefacts: group under `artifacts/research/`.
- Avoid large binaries unless part of an official release snapshot; prefer text manifests and checksums referencing external storage.

Diagnostics (`diagnostics/`)
- For lightweight, human-auditable summaries of validation and checks.
- Layout: tool/topic subfolders (linting, typing, testing, security, doctor).
- Prefer `.txt`/`.md`; limit JSON/CSV to essential, latest-only snapshots.

Naming & timestamps
- Use UTC timestamps: `YYYYMMDDThhmmssZ`.
- Include subject in filenames, e.g., `devsynth_run_tests_fast_medium_20251001T234102Z.txt`.

Retention
- Keep latest diagnostics per tool/topic; prune superseded snapshots.
- Keep release artefacts under `releases/` for the lifetime of the release series.

Governance
- Changes to this policy require PR review. Update READMEs under both directories accordingly.
