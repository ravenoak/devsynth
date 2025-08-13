---
title: Requirements Wizard Logging
author: DevSynth Team
date: 2025-02-14
status: draft
---

# Summary

Defines expected logging behaviour for the requirements wizard, including structured JSON fields and persistence rules.

## Socratic Checklist
- What is the problem?
- What proofs confirm the solution?

## Motivation

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

- A failing BDD scenario captures logging expectations.
- Unit tests verify logger handling of `exc_info` and reserved `extra` keys without errors.
- Requirements wizard persists `priority` and `constraints` after navigating backwards.
