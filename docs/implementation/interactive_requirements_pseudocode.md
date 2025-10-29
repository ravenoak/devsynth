---

author: DevSynth Team
date: '2025-06-16'
last_reviewed: '2025-09-22'
status: review
tags:

- implementation
- pseudocode
- uxbridge

title: Interactive Requirements Collection Pseudocode
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Implementation</a> &gt; Interactive Requirements Collection Pseudocode
</div>

# Interactive Requirements Collection Pseudocode

The CLI and WebUI share a `UXBridge` abstraction that prompts for requirements and persists answers through a common `MemoryManager`. Both surfaces drive the same wizard so question ordering, validation, and storage remain consistent.

```python
from devsynth.interface.ux_bridge import UXBridge
from devsynth.application.memory.adapters.tinydb_memory_adapter import TinyDBMemoryAdapter
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.requirements.wizard import RequirementsWizard

def interactive_requirements_flow(bridge: UXBridge) -> None:
    memory = MemoryManager(adapters={"tinydb": TinyDBMemoryAdapter()})
    wizard = RequirementsWizard(bridge=bridge, memory=memory)

    wizard.start_session()
    wizard.collect_project_metadata()
    wizard.collect_functional_requirements()
    wizard.collect_non_functional_requirements()
    wizard.review_and_confirm()
    wizard.finish()
```

Each wizard stage routes prompts through the provided bridge (CLI or WebUI), validates responses, and writes them to TinyDB-backed memory for later orchestration.

## Evidence

- Behavior suites [`tests/behavior/features/interactive_requirements_wizard.feature`](../../tests/behavior/features/interactive_requirements_wizard.feature), [`tests/behavior/features/interactive_requirements_flow_cli.feature`](../../tests/behavior/features/interactive_requirements_flow_cli.feature), [`tests/behavior/features/interactive_requirements_flow_webui.feature`](../../tests/behavior/features/interactive_requirements_flow_webui.feature), and [`tests/behavior/features/interactive_requirements_gathering.feature`](../../tests/behavior/features/interactive_requirements_gathering.feature) execute the wizard across both interfaces using [`tests/behavior/steps/test_interactive_requirements_steps.py`](../../tests/behavior/steps/test_interactive_requirements_steps.py).
- Unit suites [`tests/unit/application/requirements/test_wizard.py`](../../tests/unit/application/requirements/test_wizard.py), [`tests/unit/application/requirements/test_interactions.py`](../../tests/unit/application/requirements/test_interactions.py), and [`tests/unit/application/requirements/test_conversation_logging.py`](../../tests/unit/application/requirements/test_conversation_logging.py) assert prompt sequencing, validation rules, logging, and memory writes.
- Integration coverage in [`tests/integration/general/test_run_pipeline_command.py`](../../tests/integration/general/test_run_pipeline_command.py) and [`tests/integration/general/test_end_to_end_workflow.py`](../../tests/integration/general/test_end_to_end_workflow.py) shows requirement sessions populating memory during broader DevSynth workflows.

## Implementation Notes

- `devsynth.application.requirements.cli_flow.run_interactive_flow` instantiates a `ConsoleUXBridge` and the wizard to drive CLI sessions.
- The WebUI leverages `devsynth.webui.requirements.state.RequirementsStateMachine` to mirror the same wizard steps through Streamlit components while persisting to the shared memory manager.
- Memory persistence defaults to `TinyDBMemoryAdapter`, but the test suite toggles in-memory adapters to validate behavior under different storage backends.
