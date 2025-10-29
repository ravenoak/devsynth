---

title: "UXBridge Interface Extension"
date: "2025-06-19"
last_reviewed: "2025-07-20"
version: "0.1.0a1"
tags:
  - "specification"
  - "ux"
  - "cli"
  - "webui"
status: "draft"
author: "DevSynth Team"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Specifications</a> &gt; UXBridge Interface Extension
</div>

# UXBridge Interface Extension

This document defines the extended interaction methods that allow DevSynth's
workflow logic to remain UI agnostic. The updated API introduces more
descriptive names so that new front‑ends like the WebUI and Agent API can reuse
the same workflows without modification.

## Requirements

1. **ask_question(message, choices=None, default=None, show_default=True)**
   - Present a question to the user and return their response.
   - Optionally provide a list of choices and a default value.
2. **confirm_choice(message, default=False)**
   - Ask the user to confirm an action and return ``True`` or ``False``.
3. **display_result(message, highlight=False)**
   - Output a message to the user. When ``highlight`` is ``True`` the
     implementation may emphasize the text.
4. Legacy methods ``prompt``, ``confirm`` and ``print`` must remain as aliases
   for backward compatibility.
5. Implementations MUST avoid direct ``input()`` or ``print()`` calls and use
   the bridge instead so that workflows behave consistently across interfaces.

## Rationale

The original bridge exposed minimal methods which tightly coupled the CLI to the
workflow code. As additional interfaces were introduced it became necessary to
abstract user interactions behind a stable API. These methods map cleanly to
both textual and graphical UIs and allow tests to mock the interface easily.

## Design Choices

- **Clear Method Semantics** – New method names explicitly describe user
  interactions to reduce confusion when multiple front‑ends coexist.
- **Alias Support** – Backward compatibility is preserved via the legacy
  `prompt`, `confirm` and `print` methods.
- **Testability** – By avoiding direct `input()`/`print()` calls, workflows can
  be unit tested without patching built‑ins.

## Constraints

- Implementations must not directly read from or write to STDOUT/STDIN.
- Methods should return data types appropriate for the calling interface.
- Bridge implementations are responsible for rendering choice lists and
  highlights.

## Expected Behaviour

- CLI, WebUI and Agent API layers call these methods when interacting with the
  user.
- The same workflow code runs identically regardless of the active interface.

## Implementation Status

This feature is **implemented**. See `src/devsynth/interface/ux_bridge.py` for the reference implementation.

## What proofs confirm the solution?
- BDD scenarios in [`tests/behavior/features/uxbridge_extension.feature`](../../tests/behavior/features/uxbridge_extension.feature) ensure termination and expected outcomes.
- Finite state transitions and bounded loops guarantee termination.
