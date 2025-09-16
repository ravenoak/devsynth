---
author: DevSynth Team
date: '2025-09-16'
status: draft
tags:
- implementation
- invariants
title: Output Formatter Invariants
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Implementation</a> &gt; Output Formatter Invariants
</div>

# Output Formatter Invariants

The output formatter underpins cross-interface UX by ensuring that the CLI, WebUI, and Agent API all display sanitized, styled information consistently. These invariants codify the formatter's contract so interface maintainers can reason about formatting guarantees before integrating new renderers or error views.

## Formatting Rules

- **Mandatory sanitization:** All public entry points delegate to `sanitize_output`, which rejects `None`, short-circuits on empty strings, and escapes HTML when sanitization is enabled. No formatter method is permitted to bypass sanitization when rendering user-supplied content.
- **Semantic styling:** `format_message` maps detected message types to Rich styles (`bold red` for errors, `yellow` for warnings, `green` for success, `cyan` for info) and converts markdown headings into emphasis while preserving sanitized text. Highlighted messages always render inside a Rich `Panel` so that downstream bridges can rely on consistent emphasis behavior.
- **Structured output selection:** `format_structured` honors the requested `OutputFormat` and automatically falls back to text formatting for non-tabular payloads requested as tables. JSON and YAML responses are pretty-printed with `indent=self.indent`, and Rich renderables (tables, panels, syntax blocks) are returned when a console is configured.

### Example

```python
from rich.console import Console

from devsynth.interface.output_formatter import OutputFormatter

formatter = OutputFormatter()
formatter.set_console(Console())
formatter.display("SUCCESS: Tests completed", highlight=True)
```

The example above guarantees sanitized content and produces a `Panel` styled `bold white on blue`, satisfying the highlight invariant while preserving semantic coloring for downstream consumers.

## Error Handling Properties

- **Sanitization guardrails:** Passing `None` into `sanitize_output` raises `AttributeError`, enforcing explicit handling of missing text.
- **Console availability:** Calling `display` without assigning a Rich `Console` raises `ValueError`, preventing silent output drops in headless contexts. Highlighted calls rely on this guard to ensure the `Panel` can be printed with the expected emphasis style.
- **Format fallback safety:** When a caller requests table output for data that is neither a mapping nor a list of mappings, the formatter automatically replays the request through the plain-text branch so callers still receive readable output instead of runtime errors.

## Traceability

- Sanitization and styling guarantees: [tests/unit/interface/test_output_formatter_core_behaviors.py](../../tests/unit/interface/test_output_formatter_core_behaviors.py)
- Display highlight contract and console guard: [tests/unit/interface/test_output_formatter_core_behaviors.py](../../tests/unit/interface/test_output_formatter_core_behaviors.py) (`test_display_highlight_branch_emits_panel`, `test_display_without_console_raises_value_error`)

## Issue Reference

- [Coverage below threshold](../../issues/coverage-below-threshold.md)
