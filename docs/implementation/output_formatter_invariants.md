---
author: DevSynth Team
date: '2025-09-16'
status: review
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

- **Mandatory sanitization:** All public entry points delegate to `sanitize_output`, which rejects `None`, short-circuits on empty strings, and escapes HTML when sanitization is enabled. No formatter method is permitted to bypass sanitization when rendering user-supplied content. The fast regression suite exercises the delegate path, the empty-string guard, and the exception raised for `None` inputs in `test_sanitize_output_delegates_and_handles_edge_cases`.【F:tests/unit/interface/test_output_formatter_core_behaviors.py†L14-L45】
- **Semantic styling:** `format_message` maps detected message types to Rich styles (`bold red` for errors, `yellow` for warnings, `green` for success, `cyan` for info) and converts markdown headings into emphasis while preserving sanitized text. Highlighted messages always render inside a Rich `Panel` so that downstream bridges can rely on consistent emphasis behavior. `test_detect_message_type_covers_known_patterns` and `test_format_message_applies_status_styles` assert the semantic mapping, while `test_display_highlight_branch_emits_panel` covers the emphasis contract.【F:tests/unit/interface/test_output_formatter_core_behaviors.py†L47-L137】
- **Structured output selection:** `format_structured` honors the requested `OutputFormat` and automatically falls back to text formatting for non-tabular payloads requested as tables. JSON and YAML responses are pretty-printed with `indent=self.indent`, and Rich renderables (tables, panels, syntax blocks) are returned when a console is configured. The fallbacks for scalars and heterogeneous sequences, the renderable selection for rich payloads, and the handling of complex table cells are asserted by `test_table_format_falls_back_to_text_for_nontabular_inputs`, `test_rich_format_selects_renderables_for_data_shapes`, and `test_list_of_dicts_table_renders_missing_and_complex_values`. Command overrides and YAML formatting behaviors are locked in by `test_set_format_options_and_command_output_overrides`.【F:tests/unit/interface/test_output_formatter_fallbacks.py†L28-L146】

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

- **Sanitization guardrails:** Passing `None` into `sanitize_output` raises `AttributeError`, enforcing explicit handling of missing text.【F:tests/unit/interface/test_output_formatter_core_behaviors.py†L14-L45】
- **Console availability:** Calling `display` without assigning a Rich `Console` raises `ValueError`, preventing silent output drops in headless contexts. Highlighted calls rely on this guard to ensure the `Panel` can be printed with the expected emphasis style.【F:tests/unit/interface/test_output_formatter_core_behaviors.py†L107-L149】
- **Format fallback safety:** When a caller requests table output for data that is neither a mapping nor a list of mappings, the formatter automatically replays the request through the plain-text branch so callers still receive readable output instead of runtime errors.【F:tests/unit/interface/test_output_formatter_fallbacks.py†L28-L78】

## Traceability

- Specification: [docs/specifications/cross-interface-consistency.md](../../docs/specifications/cross-interface-consistency.md) defines consistent styling across delivery surfaces.【F:docs/specifications/cross-interface-consistency.md†L1-L40】
- Behavior coverage: [tests/behavior/features/general/cross_interface_consistency.feature](../../tests/behavior/features/general/cross_interface_consistency.feature) ties the formatter contract to CLI, WebUI, and API workflows.【F:tests/behavior/features/general/cross_interface_consistency.feature†L1-L40】
- Unit coverage:
  - Sanitization, semantic styling, and highlight panel guarantees are verified in [tests/unit/interface/test_output_formatter_core_behaviors.py](../../tests/unit/interface/test_output_formatter_core_behaviors.py).【F:tests/unit/interface/test_output_formatter_core_behaviors.py†L14-L149】
  - Structured output fallbacks, renderable selection, and command overrides are validated in [tests/unit/interface/test_output_formatter_fallbacks.py](../../tests/unit/interface/test_output_formatter_fallbacks.py).【F:tests/unit/interface/test_output_formatter_fallbacks.py†L28-L146】

## Issue Reference

- [Coverage below threshold](../../issues/coverage-below-threshold.md)
