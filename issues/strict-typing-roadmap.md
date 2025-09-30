Title: Strict typing roadmap
Date: 2025-09-13 00:00 UTC
Status: open
Affected Area: typing
Reproduction:
  - N/A (planning issue)
Exit Code: N/A
Artifacts:
  - N/A
Inventory (2025-09-13):
  - restore-strict-typing-adapters-requirements.md
  - ~~restore-strict-typing-adapters.md~~
  - restore-strict-typing-application-documentation.md
  - ~~restore-strict-typing-application-edrr.md~~
  - restore-strict-typing-application-memory-adapters.md
  - restore-strict-typing-application-performance.md
  - ~~restore-strict-typing-cli.md~~
  - restore-strict-typing-core-mvu.md
  - restore-strict-typing-domain-models-requirement.md
  - restore-strict-typing-domain.md
  - restore-strict-typing-edrr-reasoning-loop.md
  - restore-strict-typing-exceptions.md
  - restore-strict-typing-feature-markers.md
  - restore-strict-typing-inspect-code-cmd.md
  - restore-strict-typing-logger.md
  - restore-strict-typing-methodology-sprint.md
  - restore-strict-typing-methodology.md
  - restore-strict-typing-testing.md
Suspected Cause: Multiple open 'restore-strict-typing-*' tickets lack consolidation.
Next Actions:
  - [x] Inventory all 'restore-strict-typing-*' issues.
  - [x] Prioritize modules and schedule PRs by creating follow-up issues with owners and timelines.
Resolution Evidence:
  - Inventory recorded 2025-09-13.
  - 2025-09-14: `restore-strict-typing-cli.md` completed; removed remaining type ignore in `mvu_report_cmd` and verified `poetry run mypy src/devsynth/application/cli/commands/mvu_report_cmd.py`.
  - 2025-09-30: Adapter backlog and application workflow overrides removed; strict sweeps archived as `diagnostics/mypy_strict_adapters_20250930T201103Z.txt`, `diagnostics/mypy_strict_application_orchestration_20250930T201117Z.txt`, and `diagnostics/mypy_strict_application_prompts_20250930T201132Z.txt` with `pyproject.toml` overrides deleted.【F:diagnostics/mypy_strict_adapters_20250930T201103Z.txt†L1-L2】【F:diagnostics/mypy_strict_application_orchestration_20250930T201117Z.txt†L1-L2】【F:diagnostics/mypy_strict_application_prompts_20250930T201132Z.txt†L1-L2】【F:pyproject.toml†L285-L309】
