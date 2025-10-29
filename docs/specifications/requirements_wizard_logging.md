---
title: Requirements Wizard Logging
author: DevSynth Team
date: 2025-02-14
last_reviewed: 2025-09-19
status: review
version: 0.1.0a1
tags:
  - specification
  - logging
---

# Summary

Defines expected logging behaviour for the requirements wizard, including structured JSON fields and persistence rules.

See [Requirements Wizard Logging feature](../features/requirements_wizard_logging.md) for an overview.

## Socratic Checklist
- What is the problem?
- What proofs confirm the solution?

## Motivation

## What proofs confirm the solution?

- BDD scenarios in [`tests/behavior/requirements_wizard/features/general/requirements_wizard_logging.feature`](../../tests/behavior/requirements_wizard/features/general/requirements_wizard_logging.feature) and [`tests/behavior/requirements_wizard/features/general/logging_and_priority.feature`](../../tests/behavior/requirements_wizard/features/general/logging_and_priority.feature) exercise structured logging and priority persistence end to end.
- Unit tests in [`tests/unit/application/requirements/test_wizard.py`](../../tests/unit/application/requirements/test_wizard.py) assert that `wizard_step` entries are recorded and that `requirements_save_failed` captures `exc_info`.
- Additional persistence checks in [`tests/unit/application/requirements/test_interactions.py`](../../tests/unit/application/requirements/test_interactions.py) confirm the saved JSON mirrors logged selections.
- WebUI logging parity is maintained via [`docs/implementation/webui_rendering_invariants.md`](../implementation/webui_rendering_invariants.md).

## Intended Behaviors

- **Step tracing** – Every wizard prompt emits a JSON-formatted `wizard_step` entry capturing `step` and `value` fields.
- **Success auditing** – A `requirements_saved` entry records the final priority and persists alongside the saved file.
- **Failure visibility** – Errors surfaced while writing configuration emit `requirements_save_failed` with `exc_info` populated for diagnostic tooling.


Reliable logs ensure troubleshooting and compliance for requirement gathering flows. This specification outlines the structure for log entries and where they are stored.

## Specification

### Log Structure

Each log entry produced by the requirements wizard SHALL contain:

- `timestamp`: ISO-8601 timestamp of the event.
- `level`: severity such as `INFO` or `ERROR`.
- `logger`: emitting logger name.
- `message`: human readable text.
- `module`, `function`, `line`: resolved call site.
- `actual_module`, `actual_function`, `actual_line`: original call site prior to overrides.
- `request_id` and `phase` when available from context.
- `exception` object with `type`, `message`, and `traceback` when an error occurs.
- Arbitrary extra fields supplied via logging `extra` kwargs after filtering reserved keys.

### Persistence Rules

- Logs SHALL be written in JSON lines format to the configured log file (default `logs/devsynth.log`).
- The log directory SHALL only be created when `configure_logging` is invoked.
- When the environment variable `DEVSYNTH_NO_FILE_LOGGING` is set to `1`, file logging SHALL be disabled.
- Log records MUST survive navigation between wizard steps and reflect the last recorded state for `priority` and `constraints`.

## Acceptance Criteria

- Each wizard prompt emits a `wizard_step` log entry containing the selected value.
- Successful persistence writes a `requirements_saved` entry capturing the recorded priority and constraints.
- When configuration persistence fails, the wizard logs `requirements_save_failed` with populated `exc_info` before raising the exception.
