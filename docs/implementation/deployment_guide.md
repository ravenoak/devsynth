---
author: DevSynth Team
date: '2025-08-17'
last_reviewed: '2025-08-17'
status: active
tags:
- implementation
- deployment
title: DevSynth Deployment Guide
version: '0.1.0a1'
---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Implementation</a> &gt; DevSynth Deployment Guide
</div>

# DevSynth Deployment Guide

This guide outlines prerequisites and usage for the deployment scripts under `scripts/deployment/`.

## Prerequisites

- Docker with `docker compose` installed and accessible in `PATH`
- `curl` available for health checks
- An environment file named `.env.<environment>` with `600` permissions
- A non-root user; scripts refuse to run when executed as root

## Usage

### Bootstrapping the stack

Build images and start services for an environment:

```bash
scripts/deployment/bootstrap.sh <environment>
```

### Deploying

Pull, build, and launch the stack with a health check:

```bash
scripts/deployment/deploy.sh <environment>
```

### Controlling the stack

Start or stop services:

```bash
scripts/deployment/start_stack.sh <environment>
scripts/deployment/stop_stack.sh <environment>
```

### Publishing images

Build and push an image to the registry:

```bash
scripts/deployment/publish_image.sh <tag> <service>
```

All commands enforce the prerequisites above and provide descriptive errors when requirements are unmet.
