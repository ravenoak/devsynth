---

author: DevSynth Team
date: '2025-07-10'
last_reviewed: '2025-07-10'
status: draft
tags:
- developer-guides
- deployment
- docker
title: Deployment Setup
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; Deployment Setup
</div>

# Deployment Setup

This short guide explains how to run DevSynth locally using Docker Compose and the optional ChromaDB service.

## Quick Start

1. Install all optional extras so that ChromaDB support is available:

```bash
poetry install --all-extras
```

2. Launch the containers:

```bash
docker compose up -d chromadb devsynth
```

The `chromadb` service provides a persistent vector database. Configure the memory system by adding the following to `.devsynth/project.yaml`:

```yaml
memory_backend: chromadb
```

With this setting `docker-compose.yml` will start DevSynth with ChromaDB at `http://localhost:8001`.

## Shutdown

Stop the running containers when finished:

```bash
docker compose down
```
