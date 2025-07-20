---
title: "Agent API Reference"
date: "2025-06-19"
version: "0.1.0"
tags:
  - "api"
  - "reference"
  - "user-guide"

status: "draft"
author: "DevSynth Team"
---

# Agent API Reference

This guide demonstrates how to interact with DevSynth programmatically using the stubbed Agent API. The API mirrors CLI behaviour through the `UXBridge` layer.

## Available Endpoints

- `POST /init` – initialize or onboard a project
- `POST /gather` – collect project goals and constraints
- `POST /synthesize` – run the synthesis pipeline
- `GET /status` – fetch messages from the most recent invocation


All requests must include the bearer token header `Authorization: Bearer <token>`.

### Example Usage

```python
import requests

base = "http://localhost:8000"
headers = {"Authorization": "Bearer my-token"}

resp = requests.post(
    f"{base}/init",
    json={"path": ".", "language": "python"},
    headers=headers,
)
print(resp.json())
```
## Implementation Status

This feature is **planned** and not yet implemented.
