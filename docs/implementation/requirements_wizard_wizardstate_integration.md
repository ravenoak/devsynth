---
author: DevSynth Team
date: '2025-07-31'
last_reviewed: "2025-07-31"
status: draft
tags:
- implementation
- webui
- wizard
- state-management
title: Requirements Wizard WizardState Integration Guide
version: 0.1.0---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Implementation</a> &gt; Requirements Wizard WizardState Integration Guide
</div>

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Implementation</a> &gt; Requirements Wizard WizardState Integration Guide
</div>

# Requirements Wizard WizardState Integration Guide

This document provides a detailed guide for integrating the `WizardState` class with the requirements wizard in the WebUI. The `WizardState` class provides a more robust and consistent way to manage wizard state, with proper error handling, logging, and navigation controls.

## Current Implementation

The current requirements wizard implementation in `webui.py` uses direct session state management with functions like `get_session_value` and `set_session_value`, which are wrappers around `WebUIBridge` methods. It manages wizard state using session state variables like "wizard_step" and "wizard_data".

## Target Implementation

The target implementation will use the `WizardState` class to manage the wizard state, similar to how the gather wizard is implemented. This will provide a more consistent and robust way to manage wizard state across all wizards in the WebUI.

## Implementation Steps

### 1. Import the WizardState Class

Add the following import at the beginning of the `_requirements_wizard` method:

```python
from devsynth.interface.webui_state import WizardState
```

### 2. Create a WizardState Instance

Replace the current wizard state initialization with a `WizardState` instance:

```python
# Initialize the wizard state if it doesn't exist
wizard_name = "requirements_wizard"
steps = 5  # ["Title", "Description", "Type", "Priority", "Constraints"]
initial_state = {
    "title": os.environ.get("DEVSYNTH_REQ_TITLE", ""),
    "description": os.environ.get("DEVSYNTH_REQ_DESCRIPTION", ""),
    "type": os.environ.get("DEVSYNTH_REQ_TYPE", RequirementType.FUNCTIONAL.value),
    "priority": os.environ.get("DEVSYNTH_REQ_PRIORITY", RequirementPriority.MEDIUM.value),
    "constraints": os.environ.get("DEVSYNTH_REQ_CONSTRAINTS", ""),
}

# Check if we already have a wizard state
if not hasattr(st.session_state, f"{wizard_name}_current_step"):
    # Create a new WizardState instance
    wizard_state = WizardState(wizard_name, steps, initial_state)
else:
    # Use the existing WizardState instance
    wizard_state = WizardState(wizard_name, steps)
```

### 3. Update Step Display

Replace the current step display with `WizardState` methods:

```python
current_step = wizard_state.get_current_step()
step_names = ["Title", "Description", "Type", "Priority", "Constraints"]
st.write(f"Step {current_step} of {wizard_state.get_total_steps()}: {step_names[current_step - 1]}")
st.progress(current_step / wizard_state.get_total_steps())
```

### 4. Update Step Handling

Replace the current step handling with `WizardState` methods:

```python
try:
    if current_step == 1:
        title = st.text_input("Requirement Title", wizard_state.get("title", ""))
        wizard_state.set("title", title)
    elif current_step == 2:
        description = st.text_area("Requirement Description", wizard_state.get("description", ""))
        wizard_state.set("description", description)
    elif current_step == 3:
        options = [t.value for t in RequirementType]
        # Handle case where type is not in options
        current_type = wizard_state.get("type", RequirementType.FUNCTIONAL.value)
        try:
            index = options.index(current_type)
        except ValueError:
            index = 0
            wizard_state.set("type", options[0])
        selected_type = st.selectbox("Requirement Type", options, index=index)
        wizard_state.set("type", selected_type)
    elif current_step == 4:
        options = [p.value for p in RequirementPriority]
        # Handle case where priority is not in options
        current_priority = wizard_state.get("priority", RequirementPriority.MEDIUM.value)
        try:
            index = options.index(current_priority)
        except ValueError:
            index = 0
            wizard_state.set("priority", options[0])
        selected_priority = st.selectbox("Requirement Priority", options, index=index)
        wizard_state.set("priority", selected_priority)
    elif current_step == 5:
        constraints = st.text_area("Constraints (comma separated)", wizard_state.get("constraints", ""))
        wizard_state.set("constraints", constraints)
except Exception as e:
    # Handle any UI rendering errors gracefully
    logger.error(f"Error rendering wizard step: {str(e)}")
    self.display_result(
        f"[red]ERROR rendering wizard step: {e}[/red]",
        highlight=False,
    )
```

### 5. Update Navigation Buttons

Replace the current navigation buttons with `WizardState` navigation methods:

```python
# Navigation buttons
col1, col2, col3 = st.columns(3)

# Previous button (disabled on first step)
if current_step > 1:
    if col1.button("Previous", key="previous_button"):
        wizard_state.previous_step()

# Next button (on steps 1-4)
if current_step < wizard_state.get_total_steps():
    if col2.button("Next", key="next_button"):
        if validate_step(wizard_state, current_step):
            wizard_state.next_step()
        else:
            self.display_result("Please fill in all required fields", message_type="error")

# Save button (on last step)
if current_step == wizard_state.get_total_steps():
    if col2.button("Save Requirements", key="save_button"):
        if validate_step(wizard_state, current_step):
            try:
                result = {
                    "title": wizard_state.get("title"),
                    "description": wizard_state.get("description"),
                    "type": wizard_state.get("type"),
                    "priority": wizard_state.get("priority"),
                    "constraints": [
                        c.strip() for c in wizard_state.get("constraints", "").split(",") if c.strip()
                    ],
                }
                with open("requirements_wizard.json", "w", encoding="utf-8") as f:
                    f.write(json.dumps(result, indent=2))
                self.display_result(
                    "[green]Requirements saved to requirements_wizard.json[/green]",
                    message_type="success"
                )
                # Mark the wizard as completed
                wizard_state.set_completed(True)
                # Reset wizard state
                wizard_state.reset()
                return result
            except Exception as exc:
                self.display_result(
                    f"[red]ERROR saving requirements: {exc}[/red]",
                    message_type="error",
                    highlight=False,
                )
                return None
        else:
            self.display_result("Please fill in all required fields", message_type="error")

# Cancel button
if col3.button("Cancel", key="cancel_button"):
    # Reset the wizard state
    wizard_state.reset()
    self.display_result("Requirements wizard cancelled", message_type="info")
```

### 6. Add Validation Function

Add a validation function to validate each step:

```python
def validate_step(wizard_state, step):
    """Validate the current step."""
    if step == 1:
        return wizard_state.get("title", "") != ""
    elif step == 2:
        return wizard_state.get("description", "") != ""
    elif step == 3:
        return wizard_state.get("type", "") != ""
    elif step == 4:
        return wizard_state.get("priority", "") != ""
    elif step == 5:
        return True  # Constraints are optional
    return True
```

## Testing

After implementing these changes, the following tests should be run to verify the integration:

1. Run the behavior tests for the requirements wizard with WizardState integration:
   ```bash
   python -m pytest tests/behavior/features/webui_requirements_wizard_with_state.feature -v
   ```

2. Manually test the requirements wizard in the WebUI to ensure it works as expected:
   - Start the WebUI
   - Navigate to the Requirements page
   - Start the requirements wizard
   - Navigate through all steps
   - Save the requirements
   - Verify that the requirements are saved correctly

## Potential Issues

1. **Session State Conflicts**: The current implementation uses session state variables like "wizard_step" and "wizard_data". The new implementation will use prefixed variables like "requirements_wizard_current_step" and "requirements_wizard_completed". Make sure there are no conflicts between these variables.

2. **Error Handling**: The current implementation has extensive error handling. Make sure the new implementation maintains or improves this error handling.

3. **Backward Compatibility**: The current implementation may be used by other parts of the code. Make sure the new implementation maintains backward compatibility or update any code that depends on the current implementation.

## Related Files

- `/src/devsynth/interface/webui.py`: Contains the requirements wizard implementation
- `/src/devsynth/interface/webui_state.py`: Contains the WizardState class
- `/tests/behavior/features/webui_requirements_wizard_with_state.feature`: Contains behavior tests for the requirements wizard with WizardState integration
- `/tests/behavior/steps/test_webui_requirements_wizard_with_state_steps.py`: Contains step definitions for the behavior tests

## Implementation Status

This integration is **planned** for the next sprint. It is part of the Phase 2 (Production Readiness) work to improve the WebUI state management.