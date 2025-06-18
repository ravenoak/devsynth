---
title: "DevSynth WebUI Reference"
date: "2025-07-01"
version: "1.0.0"
tags:
  - "webui"
  - "user-guide"
status: "draft"
author: "DevSynth Team"
---

# DevSynth WebUI Reference

The WebUI provides a Streamlit front-end that mirrors the CLI workflow commands. Start it with:

```bash
streamlit run src/devsynth/interface/webui.py
```

## Navigation

The sidebar offers the following pages:

1. **Onboarding** – initialize projects.
2. **Requirements** – generate and inspect specifications.
3. **Analysis** – analyze project code.
4. **Synthesis** – generate tests and code then run the pipeline.
5. **Config** – edit configuration values.

Each page shows progress spinners and uses collapsible sections for optional input.

For more details on individual commands see the [CLI Reference](cli_reference.md).
