---
title: DevSynth Technical Specification
date: "2025-06-01"
version: "0.1.0-alpha.1"
tags:
  - specification
status: published
author: DevSynth Team
last_reviewed: "2025-06-01"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Specifications</a> &gt; DevSynth Technical Specification
</div>

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Specifications</a> &gt; DevSynth Technical Specification
</div>

# DevSynth Technical Specification

This document summarizes the latest high‑level specification for the DevSynth project. It complements the detailed [DevSynth Specification MVP Updated](devsynth_specification_mvp_updated.md) document and is kept in sync with the implemented API.

## 1. API Overview

DevSynth exposes two FastAPI applications:

- **Internal API** (`src/devsynth/api.py`) providing `/health` and `/metrics` endpoints for basic monitoring.
- **Agent API** (`src/devsynth/interface/agentapi.py`) providing workflow endpoints such as `/init`, `/gather`, `/synthesize`, `/status`, `/spec`, `/test`, `/code`, `/doctor`, `/edrr-cycle` and an additional `/metrics` endpoint.

All endpoints require optional bearer token authentication when enabled via configuration.

## 2. Implementation Status

The API modules listed above are implemented and covered by unit and integration tests. Refer to the [Requirements Traceability Matrix](../requirements_traceability.md) for details on requirement coverage.

