---
title: "Interactive Requirements Wizard"
date: "2025-06-16"
version: "0.1.0"
tags:
  - "specification"
  - "requirements"
  - "ux"
status: "draft"
author: "DevSynth Team"
---

# Interactive Requirements Wizard

This specification describes the guided workflow for collecting
requirements and constraints. The wizard runs in both the CLI and the
Streamlit WebUI through the `UXBridge` interface.

## Workflow Overview

1. Title
2. Description
3. Requirement type
4. Priority
5. Constraints
6. Confirmation and save

The wizard allows moving backward by typing `back` in the CLI or using
the *Back* button in the WebUI. Collected data is saved to a JSON file
named `requirements_wizard.json`.
