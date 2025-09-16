---
author: AI Assistant
date: '2025-09-16'
status: active
tags:
- implementation
- invariants
title: WebUI Command Invariants
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Implementation</a> &gt; WebUI Command Invariants
</div>

# WebUI Command Invariants

The command mixin shared by the WebUI guarantees predictable resolution and
error handling for CLI integrations.

## Module Overrides Take Precedence

`CommandHandlingMixin._cli` first checks attributes on the importing module,
enabling tests to inject stubs without modifying the global CLI registry.

```python
from devsynth.interface.webui.commands import CommandHandlingMixin

class Probe(CommandHandlingMixin):
    def display_result(self, *_a, **_k):
        raise AssertionError
    def _format_error_message(self, exc: Exception) -> str:
        return str(exc)
    def _render_traceback(self, text: str) -> None:
        pass

probe = Probe()
setattr(__import__("devsynth.interface.webui"), "dummy_cmd", lambda: "ok")
assert probe._cli("dummy_cmd")() == "ok"
```

[`tests/unit/interface/test_webui_commands.py::test_cli_returns_module_attribute`](../../tests/unit/interface/test_webui_commands.py)
locks this invariant in place.

## CLI Module Fallbacks Remain Available

When module-level overrides are absent, `_cli` falls back to the lazily-imported
CLI module to locate command implementations. This keeps the WebUI aligned with
the CLI surface area without duplicating registry logic.

[`test_cli_uses_cli_module_when_available`](../../tests/unit/interface/test_webui_commands.py)
demonstrates the fallback behaviour.

## Successful Invocations Pass Through

When a command executes without raising an exception `_handle_command_errors`
returns the result untouched and emits no UI messages.

```python
probe = Probe()
result = probe._handle_command_errors(lambda value: value + 1, "unused", 2)
assert result == 3
assert probe.results == []
```

The behaviour is asserted by
[`tests/unit/interface/test_webui_commands.py::test_handle_command_errors_pass_through`](../../tests/unit/interface/test_webui_commands.py).

## User-Friendly Diagnostics

Known exception classes produce explicit guidance and optional documentation
links, while unexpected failures surface the formatted exception and traceback
without masking the root cause.

[`tests/unit/interface/test_webui_commands.py::test_handle_command_errors_specific_exceptions`](../../tests/unit/interface/test_webui_commands.py)
and
[`tests/unit/interface/test_webui_commands.py::test_handle_command_errors_generic_exception`](../../tests/unit/interface/test_webui_commands.py)
demonstrate both code paths.

## DevSynth Errors Propagate

`_handle_command_errors` deliberately re-raises `DevSynthError` subclasses so the
WebUI cannot mask application-level fault semantics.

[`test_handle_command_errors_reraises_devsynth_error`](../../tests/unit/interface/test_webui_commands.py)
asserts this contract.

## References

- Tests: `tests/unit/interface/test_webui_commands.py`
- Specification: [docs/specifications/webui-command-execution.md](../specifications/webui-command-execution.md)
