title: "Requirements Wizard"
date: "2025-09-05"
version: "0.1.0a1"
tags:
  - "requirements"
  - "cli"
status: "draft"
author: "DevSynth Team"
last_reviewed: "2025-09-05"
---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">User Guides</a> &gt; Requirements Wizard
</div>

# Requirements Wizard

The requirements wizard interactively gathers title, description, type, priority, and constraints. Each step is logged using `DevSynthLogger` so sessions can be audited.

When the wizard completes, the selected priority is persisted to `.devsynth/project.yaml` allowing subsequent commands to reference the user's choice.

Example log entry:

```json
{"logger": "devsynth.application.requirements.wizard", "step": "priority", "value": "high"}
```

After running, the configuration file includes:

```yaml
priority: high
```
