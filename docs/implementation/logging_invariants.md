---
author: DevSynth Team
date: '2025-09-14'
status: draft
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

Proof: [tests/integration/utils/test_logging_integration.py](../../tests/integration/utils/test_logging_integration.py) validates the configured project logger.

## Handler Wiring Across Contexts

CLI invocations preserve both console rendering and structured JSON output. `tests/unit/logging/test_logging_setup_contexts.py::test_cli_context_wires_console_and_json_file_handlers` configures the logger with environment overrides and asserts the file handler writes JSON payloads while the console handler retains the default formatter.

## Console-Only Mode and Test Redirection

Test harnesses set `DEVSYNTH_PROJECT_DIR` to sandbox filesystem writes. `tests/unit/logging/test_logging_setup_contexts.py::test_test_context_redirects_and_supports_console_only_toggle` demonstrates that `configure_logging` redirects absolute paths underneath the project directory and that toggling `DEVSYNTH_NO_FILE_LOGGING` removes the JSON file handler while console capture continues.

## Manual JSON Toggle

`tests/unit/logging/test_logging_setup_contexts.py::test_create_dir_toggle_disables_json_file_handler` verifies that explicitly setting `create_dir=False` disables the JSON file handler even without environment flags, satisfying scenarios where CLI utilities want console-only diagnostics.

## Warning Isolation

Tests capture log output to avoid cross-test interference.

```python
import logging

logger = logging.getLogger("demo")
logger.warning("hello")
```

Simulation: [tests/integration/general/test_config_loader.py](../../tests/integration/general/test_config_loader.py) demonstrates warnings emitted under controlled logging levels.

## Issue Reference

- [logging-setup-utilities](../../issues/logging-setup-utilities.md)
