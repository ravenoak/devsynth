# Typing Relaxations Tracking (toward 2025-10-01)

Purpose: Track modules listed under [tool.mypy.overrides] in pyproject.toml with relaxations or ignore flags, and plan restoration to strict mode by 2025-10-01 as required by docs/plan.md and docs/tasks.md Task 12.

How to use this document:
- Run: poetry run python scripts/list_mypy_overrides.py
- Review diagnostics/mypy_overrides.json and identify owners for each module group.
- For each module, create a follow-up issue with a concrete checklist to remove overrides and restore strict typing.
- Update the table below with links and status.

| Module pattern | Current relaxations | Owner | Issue link | Target date | Status |
|---|---|---|---|---|---|
| devsynth.application.cli.commands.inspect_code_cmd | removed | TBD | [restore-strict-typing-inspect-code-cmd.md](restore-strict-typing-inspect-code-cmd.md) | 2025-10-01 | closed |
| devsynth.feature_markers | removed | TBD | [restore-strict-typing-feature-markers.md](restore-strict-typing-feature-markers.md) | 2025-10-01 | closed |
| devsynth.core.mvu.* | removed | core | [restore-strict-typing-core-mvu.md](restore-strict-typing-core-mvu.md) | 2025-10-01 | closed |
| devsynth.application.documentation.* | removed | TBD | [restore-strict-typing-application-documentation.md](restore-strict-typing-application-documentation.md) | 2025-10-01 | closed |
| devsynth.domain.* | removed | TBD | [restore-strict-typing-domain.md](restore-strict-typing-domain.md) | 2025-10-01 | closed |
| devsynth.application.performance | removed | TBD | [restore-strict-typing-application-performance.md](restore-strict-typing-application-performance.md) | 2025-10-01 | closed |
| devsynth.adapters.requirements.* | removed | TBD | [restore-strict-typing-adapters-requirements.md](restore-strict-typing-adapters-requirements.md) | 2025-10-01 | closed |
| devsynth.application.memory.adapters.* | removed | TBD | [restore-strict-typing-application-memory-adapters.md](restore-strict-typing-application-memory-adapters.md) | 2025-10-01 | closed |
| devsynth.exceptions | removed | TBD | [restore-strict-typing-exceptions.md](restore-strict-typing-exceptions.md) | 2025-10-01 | closed |
| devsynth.testing.* | removed | TBD | [restore-strict-typing-testing.md](restore-strict-typing-testing.md) | 2025-10-01 | closed |
| devsynth.methodology.sprint | removed | TBD | [restore-strict-typing-methodology-sprint.md](restore-strict-typing-methodology-sprint.md) | 2025-10-01 | closed |
| devsynth.logger | removed | TBD | [restore-strict-typing-logger.md](restore-strict-typing-logger.md) | 2025-10-01 | closed |
| devsynth.methodology.* | removed | TBD | [restore-strict-typing-methodology.md](restore-strict-typing-methodology.md) | 2025-10-01 | closed |
| devsynth.application.edrr.* | removed | TBD | [restore-strict-typing-application-edrr.md](restore-strict-typing-application-edrr.md) | 2025-10-01 | closed |
| devsynth.interface.agentapi_models | ignore_errors | TBD | [restore-strict-typing-interface-agentapi-models.md](restore-strict-typing-interface-agentapi-models.md) | 2025-10-01 | open |
| devsynth.interface.webui_state | ignore_errors | TBD | [restore-strict-typing-interface-webui-state.md](restore-strict-typing-interface-webui-state.md) | 2025-10-01 | open |
| devsynth.interface.enhanced_error_handler | ignore_errors | TBD | [restore-strict-typing-interface-enhanced-error-handler.md](restore-strict-typing-interface-enhanced-error-handler.md) | 2025-10-01 | open |
| devsynth.interface.ux_bridge | ignore_errors | TBD | [restore-strict-typing-interface-ux-bridge.md](restore-strict-typing-interface-ux-bridge.md) | 2025-10-01 | open |
| devsynth.interface.wizard_state_manager | ignore_errors | TBD | [restore-strict-typing-interface-wizard-state-manager.md](restore-strict-typing-interface-wizard-state-manager.md) | 2025-10-01 | open |
| devsynth.interface.progress_utils | ignore_errors | TBD | [restore-strict-typing-interface-progress-utils.md](restore-strict-typing-interface-progress-utils.md) | 2025-10-01 | open |
| devsynth.interface.output_formatter | ignore_errors | TBD | [restore-strict-typing-interface-output-formatter.md](restore-strict-typing-interface-output-formatter.md) | 2025-10-01 | open |
| devsynth.interface.simple_run | ignore_errors | TBD | [restore-strict-typing-interface-simple-run.md](restore-strict-typing-interface-simple-run.md) | 2025-10-01 | open |
| devsynth.interface.shared_bridge | ignore_errors | TBD | [restore-strict-typing-interface-shared-bridge.md](restore-strict-typing-interface-shared-bridge.md) | 2025-10-01 | open |
| devsynth.interface.command_output | ignore_errors | TBD | [restore-strict-typing-interface-command-output.md](restore-strict-typing-interface-command-output.md) | 2025-10-01 | open |
| devsynth.interface.webui_bridge | ignore_errors | TBD | [restore-strict-typing-interface-webui-bridge.md](restore-strict-typing-interface-webui-bridge.md) | 2025-10-01 | open |
| devsynth.interface.webui.rendering | ignore_errors | TBD | [restore-strict-typing-interface-webui-rendering.md](restore-strict-typing-interface-webui-rendering.md) | 2025-10-01 | open |
| devsynth.interface.research_telemetry | ignore_errors | TBD | [restore-strict-typing-interface-research-telemetry.md](restore-strict-typing-interface-research-telemetry.md) | 2025-10-01 | open |
| devsynth.interface.nicegui_webui | ignore_errors | TBD | [restore-strict-typing-interface-nicegui-webui.md](restore-strict-typing-interface-nicegui-webui.md) | 2025-10-01 | open |
| devsynth.interface.dpg_bridge | ignore_errors | TBD | [restore-strict-typing-interface-dpg-bridge.md](restore-strict-typing-interface-dpg-bridge.md) | 2025-10-01 | open |
| devsynth.interface.cli | ignore_errors | TBD | [restore-strict-typing-interface-cli.md](restore-strict-typing-interface-cli.md) | 2025-10-01 | open |
| devsynth.interface.agentapi | ignore_errors | TBD | [restore-strict-typing-interface-agentapi.md](restore-strict-typing-interface-agentapi.md) | 2025-10-01 | open |
| devsynth.interface.agentapi_enhanced | ignore_errors | TBD | [restore-strict-typing-interface-agentapi-enhanced.md](restore-strict-typing-interface-agentapi-enhanced.md) | 2025-10-01 | open |
| devsynth.interface.webui.commands | ignore_errors | TBD | [restore-strict-typing-interface-webui-commands.md](restore-strict-typing-interface-webui-commands.md) | 2025-10-01 | open |
| devsynth.interface.mvuu_dashboard | ignore_errors | TBD | [restore-strict-typing-interface-mvuu-dashboard.md](restore-strict-typing-interface-mvuu-dashboard.md) | 2025-10-01 | open |
| devsynth.interface.webui_setup | ignore_errors | TBD | [restore-strict-typing-interface-webui-setup.md](restore-strict-typing-interface-webui-setup.md) | 2025-10-01 | open |
| devsynth.interface.dpg_ui | ignore_errors | TBD | [restore-strict-typing-interface-dpg-ui.md](restore-strict-typing-interface-dpg-ui.md) | 2025-10-01 | open |
| devsynth.application.cli.__init__ | ignore_errors | TBD | [restore-strict-typing-cli.md](restore-strict-typing-cli.md) | 2025-10-01 | open |

## Targeted checklist (2025-10-04)

- [x] Audit `devsynth.application.cli.commands` for lingering `type: ignore` suppressions and replace them with typed helpers in `dpg_cmd` and `webui_cmd`.
- [x] Verify `devsynth.application.cli.long_running_progress` exposes a protocol-safe boundary for progress indicators without suppression.
- [x] Confirm `devsynth.testing.run_tests` satisfies strict typing with explicit command contracts and no `type: ignore` usage.
- [x] Remove the corresponding module patterns from the `ignore_errors = true` allowlist in `pyproject.toml` after the strict run passes.

Notes:
- This table is seeded automatically from pyproject.toml relaxations as of 2025-09-02. Keep it updated as overrides are narrowed or removed.
- Add TODO comments in modules when touching code to remind about the strictness restoration deadline.
- 2025-09-10: Removed the mypy override for `devsynth.cli` after upgrading Typer to a typed release.
- 2025-09-14: Removed the mypy override for `devsynth.methodology.edrr.reasoning_loop` after adding type annotations.
- 2025-09-13: Removed the mypy override for `devsynth.adapters.*` after restoring type coverage.
- 2025-09-13: Attempted to remove the `devsynth.application.edrr.*` override, but `poetry run mypy src/devsynth/application/edrr`
  reported 430 errors; the ignore remains in place.
- 2025-09-14: Removed the mypy override for `devsynth.application.edrr.*` after annotating EDRR modules.
- 2025-09-14: Removed the mypy override for `devsynth.exceptions` after adding type hints.
- 2025-09-14: Added `-> None` annotations for exception constructors and typed `__cause__` attributes.
- 2025-09-14: Removed the mypy override for `devsynth.feature_markers` after annotating marker functions.
- 2025-09-14: Removed the mypy override for `devsynth.adapters.requirements.*` after adding type hints.
- 2025-09-14: Audited `devsynth.domain.*`, removed override, and closed tracking; `poetry run mypy src/devsynth/domain` reports outstanding issues for future refinement.
- 2025-09-14: Removed the mypy override for `devsynth.application.performance` after adding structured metrics types.
- 2025-09-14: Removed the mypy override for `devsynth.core.mvu.*` after restoring strict typing.
- 2025-09-14: Removed the mypy overrides for `devsynth.methodology.*` and `devsynth.methodology.sprint` after enforcing strict typing.
- 2025-09-14: Removed the mypy override for `devsynth.testing.*` after clarifying helper contracts.
- 2025-09-14: Verified `devsynth.cli` uses strict typing with no remaining `type: ignore` comments.
- 2025-09-14: Restored strict typing for `devsynth.application.cli.commands.inspect_code_cmd` and removed module override.
- 2025-09-14: Removed the mypy override for `devsynth.logger` after typing handlers and log records.
- 2025-09-14: Confirmed removal of `devsynth.adapters.*` override and closed tracking issue.
- 2025-09-14: Verified removal of `devsynth.application.documentation.*` override after adding type annotations.
- 2025-09-15: Revalidated `devsynth.methodology.*` modules; no `type: ignore`
  comments remain.
- 2025-09-14: Revalidated `devsynth.testing.*`; `poetry run mypy src/devsynth/testing`
  reports no issues.
- 2025-10-06: `poetry run task mypy:strict` now fails on segmented helpers inside `devsynth.testing.run_tests`, publishing `QualityGate b2bd60e7-30cd-4b84-8e3d-4dfed0817ee3`/`TestRun 71326ec2-aa95-49dd-a600-f3672d728982`; regression evidence archived at `diagnostics/mypy_strict_20251006T212233Z.log` pending follow-up tickets.【F:diagnostics/mypy_strict_20251006T212233Z.log†L1-L32】
- 2025-10-06: `poetry run task mypy:strict` now fails on segmented helpers inside `devsynth.testing.run_tests`, publishing `QualityGate b2bd60e7-30cd-4b84-8e3d-4dfed0817ee3`/`TestRun 71326ec2-aa95-49dd-a600-f3672d728982`; regression evidence archived at `diagnostics/mypy_strict_20251006T212233Z.log` pending follow-up tickets.【F:diagnostics/mypy_strict_20251006T212233Z.log†L1-L32】
- 2025-10-06 21:44 UTC: A follow-up strict run reproduced the failure with updated knowledge-graph nodes (`TestRun 01f68130-3127-4f9e-8c2b-cd7d17485d6c`, evidence `44dce9f6-38ca-47ed-9a01-309d02418927`), captured in `diagnostics/typing/mypy_strict_20251127T000000Z.log` for ongoing triage.【F:diagnostics/typing/mypy_strict_20251127T000000Z.log†L1-L40】
