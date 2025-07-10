---
author: DevSynth Team
date: '2025-06-16'
last_reviewed: "2025-07-10"
status: draft
tags:

- implementation
- pseudocode
- uxbridge

title: UXBridge Interaction Flow
version: 0.1.0
---

# UXBridge Interaction Flow

The following example shows how both the CLI and WebUI use a common `UXBridge`
implementation with the `EDRRCoordinator`.

```python
from devsynth.interface.ux_bridge import UXBridge
from devsynth.application.EDRR.coordinator import EDRRCoordinator
from devsynth.application.memory.adapters.tinydb_memory_adapter import TinyDBMemoryAdapter
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.WSDE import WSDETeam

def run_workflow(bridge: UXBridge) -> None:
    memory = MemoryManager(adapters={"TinyDB": TinyDBMemoryAdapter()})
    coordinator = EDRRCoordinator(
        memory_manager=memory,
        wsde_team=WSDETeam(),
        code_analyzer=None,
        ast_transformer=None,
        prompt_manager=None,
        documentation_manager=None,
    )

    task = bridge.ask_question("What task should DevSynth run?")
    if bridge.confirm_choice(f"Run {task} now?"):
        coordinator.start_cycle({"description": task})
        bridge.display_result("Cycle started")
```

This shared implementation works across the command-line interface and the future WebUI.

## Current Limitations

The `UXBridge` abstraction is still conceptual. A concrete interface layer and
end-to-end tests have not yet been created, and WebUI support is incomplete.
