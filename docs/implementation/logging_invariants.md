---
author: DevSynth Team
date: '2025-09-20'
status: review
tags:
- implementation
- invariants
title: Logging Invariants
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Implementation</a> &gt; Logging Invariants
</div>

# Logging Invariants

This note outlines invariants of the logging subsystem to ensure consistent diagnostic output.

## Project Logger Consistency

`setup_logging` always returns a `DevSynthLogger` configured with the project name and level.

```python
from devsynth.utils.logging import DevSynthLogger, setup_logging

logger = setup_logging("demo", log_level=10)
assert isinstance(logger, DevSynthLogger)
assert logger.name == "demo"
```

- **Proof:** [tests/integration/utils/test_logging_integration.py](../../tests/integration/utils/test_logging_integration.py) validates the configured project logger.
- **Counterexample:** The coverage sweep leaves `_log`'s defensive branches (lines 498-548) and the facade helpers (lines 552-575) unexecuted, so we lack evidence that the wrapper preserves warning isolation when callers forward custom kwargs; see [Uncovered Branch Inventory](#uncovered-branch-inventory) &rarr; Failure remediation.【F:src/devsynth/logging_setup.py†L482-L575】【F:issues/tmp_cov_logging_setup.json†L1-L1】

## Handler Wiring Across Contexts

CLI invocations preserve both console rendering and structured JSON output.

- **Proof:** `tests/unit/logging/test_logging_setup_contexts.py::test_cli_context_wires_console_and_json_file_handlers` configures the logger with environment overrides and asserts the file handler writes JSON payloads while the console handler retains the default formatter.
- **Counterexample:** JSON formatter enrichments (lines 137-180) and the console/file handler wiring (lines 413-435 and 446-453) never execute during the sweep, leaving console/JSON parity undocumented for error and request-context payloads; see [Uncovered Branch Inventory](#uncovered-branch-inventory) &rarr; Console/JSON handler parity.【F:src/devsynth/logging_setup.py†L117-L180】【F:src/devsynth/logging_setup.py†L412-L455】【F:issues/tmp_cov_logging_setup.json†L1-L1】

## Console-Only Mode and Test Redirection

Test harnesses set `DEVSYNTH_PROJECT_DIR` to sandbox filesystem writes.

- **Proof:** `tests/unit/logging/test_logging_setup_contexts.py::test_test_context_redirects_and_supports_console_only_toggle` demonstrates that `configure_logging` redirects absolute paths underneath the project directory and that toggling `DEVSYNTH_NO_FILE_LOGGING` removes the JSON file handler while console capture continues.
- **Counterexample:** The coverage sweep misses the redirection and guard branches in both `ensure_log_dir_exists` (lines 265-304) and `configure_logging` (lines 342-373 and 405-410), so we do not yet prove that sandbox rewrites and deferred directory creation protect test isolation; see [Uncovered Branch Inventory](#uncovered-branch-inventory) &rarr; Directory-creation guards.【F:src/devsynth/logging_setup.py†L237-L310】【F:src/devsynth/logging_setup.py†L340-L410】【F:issues/tmp_cov_logging_setup.json†L1-L1】

## Manual JSON Toggle

- **Proof:** `tests/unit/logging/test_logging_setup_contexts.py::test_create_dir_toggle_disables_json_file_handler` verifies that explicitly setting `create_dir=False` disables the JSON file handler even without environment flags, satisfying scenarios where CLI utilities want console-only diagnostics.
- **Counterexample:** Coverage gaps across the retention toggles (lines 255, 260, 262, 331, 336-337, and 388) show that neither `DEVSYNTH_NO_FILE_LOGGING` nor the manual `create_dir` switch is exercised through `configure_logging`, leaving the retention matrix without runtime evidence; see [Uncovered Branch Inventory](#uncovered-branch-inventory) &rarr; Retention toggles.【F:src/devsynth/logging_setup.py†L254-L338】【F:issues/tmp_cov_logging_setup.json†L1-L1】

## Warning Isolation

Tests capture log output to avoid cross-test interference.

```python
import logging

logger = logging.getLogger("demo")
logger.warning("hello")
```

- **Proof:** [tests/integration/general/test_config_loader.py](../../tests/integration/general/test_config_loader.py) demonstrates warnings emitted under controlled logging levels.
- **Counterexample:** The absence of calls into `DevSynthLogger.warning`, `.error`, `.critical`, and `.exception` (lines 560-575) means the façade's warning isolation remains unmeasured when upstream code injects extra context, tying the gap back to [Uncovered Branch Inventory](#uncovered-branch-inventory) &rarr; Console/JSON handler parity.【F:src/devsynth/logging_setup.py†L552-L575】【F:issues/tmp_cov_logging_setup.json†L1-L1】

## Issue Reference

- [logging-setup-utilities](../../issues/logging-setup-utilities.md)

## Coverage Signal (2025-09-20)

- Focused fast tests [`tests/unit/logging/test_logging_setup_additional_paths.py`](../../tests/unit/logging/test_logging_setup_additional_paths.py) validate secret redaction, JSON formatter context, log-dir rewrites, and `DevSynthLogger._log` keyword filtering. A dedicated coverage sweep records 41.15 % line coverage for `src/devsynth/logging_setup.py`, surfacing the remaining gaps in legacy handler wiring while proving the invariants execute deterministically without touching the real filesystem.【F:tests/unit/logging/test_logging_setup_additional_paths.py†L1-L185】【F:issues/tmp_cov_logging_setup.json†L1-L1】

## Uncovered Branch Inventory

| Theme | Gap summary | Governing knobs / triggers | Coverage JSON missing lines |
| --- | --- | --- | --- |
| Retention toggles | `configure_logging` never proves that `DEVSYNTH_NO_FILE_LOGGING` or `create_dir=False` suppress JSON retention while preserving console output. | `DEVSYNTH_NO_FILE_LOGGING`, `create_dir` parameter | `255, 260, 262, 331, 336-337, 388`【F:issues/tmp_cov_logging_setup.json†L1-L1】 |
| Directory-creation guards | Sandbox rewrites and deferred directory creation paths remain untested in both `ensure_log_dir_exists` and `configure_logging`, so project-directory redirection is speculative. | `DEVSYNTH_PROJECT_DIR`, `log_dir` / `log_file` overrides | `265, 267-304, 342-349, 353, 355-356, 359, 367-373, 377, 379-380, 405-410`【F:issues/tmp_cov_logging_setup.json†L1-L1】 |
| Console/JSON handler parity | Formatter enrichments, handler attachment, and façade helpers lack coverage, leaving parity between structured JSON and console output unchecked. | `create_dir`, `DEVSYNTH_NO_FILE_LOGGING` (indirect), handler defaults | `137-138, 145-148, 173, 175-178, 180, 413, 416, 419-423, 426-435, 446-447, 450-451, 453, 562, 566, 570, 574-575`【F:issues/tmp_cov_logging_setup.json†L1-L1】 |
| Failure remediation | Defensive fallbacks for redaction errors, directory creation failures, and file-handler exceptions are not executed, leaving recovery stories unverified. | Permission failures, invalid sandbox paths, unexpected `exc_info` payloads | `111, 113, 297-303, 436, 438, 443, 498-503, 531, 534-536, 538, 542, 544, 546, 548`【F:issues/tmp_cov_logging_setup.json†L1-L1】 |
