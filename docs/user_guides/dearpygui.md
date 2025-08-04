---
author: DevSynth Team
date: "2025-08-04"
last_reviewed: "2025-08-04"
status: published
tags:
  - gui
  - user guide
  - dearpygui
title: Dear PyGui User Guide
version: 0.1.0
---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">User Guides</a> &gt; Dear PyGui User Guide
</div>

# Dear PyGui User Guide

The Dear PyGui interface provides a lightweight desktop client for DevSynth. It shares workflow logic with the CLI through the [UXBridge abstraction](../architecture/uxbridge.md), allowing commands to be reused across interfaces.

## Installation

Install the GUI extra and run the interface module:

```bash
poetry install --extras gui
poetry run python -m devsynth.interface.dpg_ui
```

## Command Mapping

The table below shows how common CLI commands map to Dear PyGui actions.

| CLI Command | Dear PyGui Action |
|-------------|------------------|
| `init`      | **Init** button |
| `inspect`   | **Inspect** button |
| `gather`    | **Gather** button |

For a full mapping of commands across interfaces, see the [CLI to WebUI and Dear PyGUI Command Mapping](../architecture/cli_webui_mapping.md).

## Screenshots

![Main window](../images/dearpygui/main_window.svg)

![Command buttons](../images/dearpygui/command_buttons.svg)
