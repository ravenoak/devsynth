---

author: DevSynth Team
date: '2025-06-18'
last_reviewed: '2025-06-18'
status: draft
tags:
  - webui
  - user-guide
title: DevSynth WebUI Reference
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">User Guides</a> &gt; DevSynth WebUI Reference
</div>

# DevSynth WebUI Reference

The WebUI provides a NiceGUI front-end that mirrors the CLI workflow commands. Start it with:

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


Each page shows progress spinners and uses collapsible sections for optional input. The server listens on port 8080 by default.

For more details on individual commands see the [CLI Reference](cli_reference.md).

## Migration Rationale

DevSynth migrated from Streamlit to NiceGUI to take advantage of server-side rendering, a richer component model, and easier integration with our existing FastAPI stack. NiceGUI also simplifies automated testing and deployment by exposing an ASGI application that can be hosted with standard tooling.

## Deployment

The NiceGUI interface can be launched locally with `devsynth webui`. For production use, serve the application with an ASGI server such as `uvicorn`:

```bash
uvicorn devsynth.interface.nicegui_webui:main --host 0.0.0.0 --port 8080
```

Container images can expose port 8080 and run the same entry point.

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

.
