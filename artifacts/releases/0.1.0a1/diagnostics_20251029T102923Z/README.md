Diagnostics artifacts

Purpose
- Store lightweight, human-auditable outputs from validation steps (pytest collection, doctor, marker verification, inventories).

Retention policy
- Keep latest per task/run; prune bulky or superseded blobs. Do not commit large binaries. Prefer .txt/.md summaries.
- For large structured outputs (JSON, CSV), store only when essential for auditability and keep one latest snapshot per tool.

Commit policy
- Repository ignores diagnostics/* by default, but whitelists .gitkeep, *.txt, *.md, and this README.md to allow curated evidence to be versioned when appropriate.
- 2025-09-29: Captured strict-typing gate artefacts for the Agent API and requirements stacks (mypy + fast/medium regression harness) so the new enforcement remains auditable.【F:diagnostics/mypy_strict_agentapi_requirements_20250929T162537Z.txt†L1-L106】【F:diagnostics/devsynth_run_tests_fast_medium_api_strict_20250929T163210Z.txt†L1-L20】
- 2025-09-30: Documented fast+medium regression attempts showing missing dependencies (CLI entry point unavailable; pytest collection blocked by numpy/GUI extras).【F:diagnostics/devsynth_run_tests_fast_medium_20250930T161600Z.txt†L1-L3】【F:diagnostics/devsynth_run_tests_fast_medium_20250930T1620_attempt.txt†L1-L11】
- 2025-09-30: Captured fast+medium retry after installing Typer, Click, PyYAML, argon2-cffi, cryptography, requests, numpy, rdflib, TinyDB, pytest, pytest-cov, pytest-bdd, and tiktoken. Collection still hit 232 marker/dependency errors; see `diagnostics/devsynth_run_tests_fast_medium_20250930T170112Z.txt` for the transcript and `diagnostics/full_profile_coverage.txt` for the gate status.【F:diagnostics/devsynth_run_tests_fast_medium_20250930T170112Z.txt†L1-L3】【F:diagnostics/full_profile_coverage.txt†L1-L19】
- 2025-10-01: Logged the fast+medium evidence drop for release rehearsal tooling. Direct invocation of `run_tests` still halts at CLI registration gaps (missing `testing` command) and Protocol typing regressions; marker verification reproduces the same collection failures alongside numerous missing feature files.【F:diagnostics/devsynth_run_tests_fast_medium_20251001T234102Z.txt†L1-L4】【F:diagnostics/verify_test_markers_stdout_20251001T234358Z.txt†L1-L40】
- 2025-10-03: Captured a clean strict typing sweep for the full `src/devsynth` tree after realigning mypy overrides for the memory stack; transcript archived at `diagnostics/mypy_strict_src_devsynth_20251003T172126Z.txt`.【F:diagnostics/mypy_strict_src_devsynth_20251003T172126Z.txt†L1-L1】

Canonical layout
- linting/ … summaries from Black/isort/ruff
- typing/ … summaries from mypy (and strict inventories)
- testing/ … pytest collection outputs, marker verification, inventories
- security/ … bandit/safety summaries and links to JSON artifacts
- doctor/ … environment and service checks

Naming
- <tool>_<subject>_<UTC timestamp>.txt (e.g., mypy_strict_src_devsynth_20251003T172126Z.txt)
