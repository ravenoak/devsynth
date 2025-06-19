---
title: "Agent API Stub"
date: "2025-06-19"
version: "0.1.0"
tags:
  - "specification"
  - "api"
status: "draft"
author: "DevSynth Team"
---

# Agent API Stub

This document outlines the minimal HTTP interface for driving DevSynth
workflows programmatically. The API mirrors the CLI and WebUI behaviour
through the `UXBridge` abstraction.

## Endpoints

### `POST /init`
Initializes or onboards a project.

Example request:
```json
{ "path": ".", "project_root": ".", "language": "python", "goals": "demo" }
```
Example response:
```json
{ "messages": ["Initialized DevSynth project"] }
```

### `POST /gather`
Collects project goals and constraints.

Example request:
```json
{
  "goals": "ai, tests",
  "constraints": "offline",
  "priority": "medium"
}
```
Example response:
```json
{ "messages": ["Requirements saved to requirements_plan.yaml"] }
```

### `POST /synthesize`
Runs the synthesis pipeline.

Example request:
```json
{ "target": "unit-tests" }
```
Example response:
```json
{ "messages": ["Execution complete."] }
```

### `GET /status`
Returns the messages from the most recent workflow invocation.

Example response:
```json
{ "messages": ["Execution complete."] }
```
