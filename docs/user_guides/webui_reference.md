---
author: DevSynth Team
date: '2025-06-18'
status: draft
tags:

- webui
- user-guide

title: DevSynth WebUI Reference
version: 0.1.0
---

# DevSynth WebUI Reference

The WebUI provides a Streamlit front-end that mirrors the CLI workflow commands. Start it with:

```bash
devsynth webui
```

## Navigation

The sidebar offers the following pages:

1. **Onboarding** – initialize projects.
2. **Requirements** – generate and inspect specifications.
3. **Analysis** – inspect project code.
4. **Synthesis** – generate tests and code then run the pipeline.
5. **Config** – edit configuration values.
6. **Diagnostics** – run environment checks via the doctor command.


Each page shows progress spinners and uses collapsible sections for optional input.

For more details on individual commands see the [CLI Reference](cli_reference.md).

### Diagnostics

Use the **Diagnostics** page to validate your configuration directly from the WebUI.
Click **Run Diagnostics** and the results of `doctor_cmd` will be displayed in the main view.

```python

# Pseudocode

def webui_button_clicked():
    # delegate to CLI workflow via UXBridge
    spec_cmd(requirements_file="req.md", bridge=self)
```
## Implementation Status

This feature is **planned** and not yet implemented.
