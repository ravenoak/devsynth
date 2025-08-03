---
title: "Requirements Wizard Structure"
date: "2025-08-03"
version: "0.1.0"
tags:
  - "developer-guide"
  - "requirements"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-08-03"
---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; Requirements Wizard Structure
</div>

# Requirements Wizard Structure

The WebUI requirements wizard has been refactored into smaller helper methods to improve
maintainability and testing. The `WebUI` class now delegates specific tasks to the
following private helpers:

- `_validate_requirements_step` – ensures required fields are provided for each step.
- `_handle_requirements_navigation` – manages navigation buttons and orchestrates saving.
- `_save_requirements` – writes collected requirements to `requirements_wizard.json` and resets state.

When extending the wizard or modifying its behaviour, update these helpers rather than
`_requirements_wizard` directly. This separation keeps validation, navigation, and
persistence logic isolated and easier to test.
