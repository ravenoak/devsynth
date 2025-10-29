---

author: DevSynth Team
date: '2025-06-16'
last_reviewed: '2025-09-22'
status: review
tags:

- implementation
- pseudocode
- uxbridge

title: UXBridge Interaction Flow
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Implementation</a> &gt; UXBridge Interaction Flow
</div>

# UXBridge Interaction Flow

`UXBridge` provides a uniform prompt/response channel consumed by CLI and WebUI flows. The coordinator and requirements wizards use the same bridge contract, allowing interface-specific adapters to forward questions and persist answers without duplicating orchestration logic.

```python
from devsynth.interface.ux_bridge import UXBridge
from devsynth.application.memory.adapters.tinydb_memory_adapter import TinyDBMemoryAdapter
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.edrr.coordinator.core import EDRRCoordinator
from devsynth.domain.models.wsde_facade import WSDETeam

def run_edrr_cycle(bridge: UXBridge) -> None:
    memory = MemoryManager(adapters={"tinydb": TinyDBMemoryAdapter()})
    coordinator = EDRRCoordinator(
        memory_manager=memory,
        wsde_team=WSDETeam(),
        code_analyzer=None,
        ast_transformer=None,
        prompt_manager=None,
        documentation_manager=None,
    )

    task_description = bridge.ask_question("What task should DevSynth run?")
    if not bridge.confirm_choice(f"Run '{task_description}' now?"):
        bridge.display_result("Request cancelled")
        return

    result = coordinator.start_cycle({"description": task_description})
    bridge.display_result(result)
```

CLI adapters expose methods like `ask_question`, `confirm_choice`, and `display_result` via the console, while Streamlit adapters render the same prompts inside the WebUI.

## Evidence

- Behavior suites [`tests/behavior/features/general/uxbridge.feature`](../../tests/behavior/features/general/uxbridge.feature), [`tests/behavior/features/general/uxbridge_cli_webui.feature`](../../tests/behavior/features/general/uxbridge_cli_webui.feature), [`tests/behavior/features/shared_uxbridge_across_cli_and_webui.feature`](../../tests/behavior/features/shared_uxbridge_across_cli_and_webui.feature), and [`tests/behavior/features/uxbridge_interface.feature`](../../tests/behavior/features/uxbridge_interface.feature) execute the bridge across both interfaces using [`tests/behavior/steps/test_uxbridge_steps.py`](../../tests/behavior/steps/test_uxbridge_steps.py) and shared helpers.
- Unit suites [`tests/unit/interface/test_uxbridge.py`](../../tests/unit/interface/test_uxbridge.py), [`tests/unit/interface/test_cli_uxbridge_noninteractive.py`](../../tests/unit/interface/test_cli_uxbridge_noninteractive.py), [`tests/unit/interface/test_uxbridge_config.py`](../../tests/unit/interface/test_uxbridge_config.py), and [`tests/unit/interface/test_uxbridge_question_result.py`](../../tests/unit/interface/test_uxbridge_question_result.py) validate CLI/WebUI adapters, sanitization rules, and logging hooks.
- Integration coverage in [`tests/integration/general/test_webui_integration.py`](../../tests/integration/general/test_webui_integration.py) and [`tests/integration/general/test_end_to_end_workflow.py`](../../tests/integration/general/test_end_to_end_workflow.py) confirms UXBridge adapters remain consistent when executing full DevSynth workflows.

## Implementation Notes

- CLI sessions use `devsynth.interface.cli.bridge.ConsoleUXBridge` to map bridge calls to console prompts.
- WebUI sessions route through `devsynth.webui.state.uxbridge.SharedUXBridge`, which proxies prompts to Streamlit components while respecting the same bridge API.
- Both adapters share middleware for sanitizing responses and logging interactions, ensuring downstream components (EDRR coordinator, requirements wizard, prompt manager) consume identical payloads regardless of interface.
