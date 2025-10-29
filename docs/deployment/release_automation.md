---
title: "Release Automation"
author: "DevSynth Team"
date: "2025-07-21"
last_reviewed: "2025-07-21"
status: "draft"
version: "0.1.0a1"
tags:
  - deployment
  - ci
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Deployment</a> &gt; Release Automation
</div>

# Release Automation

This guide describes manual image publishing and rollback for DevSynth.

## Publishing images

Manually dispatch the **Publish Docker Image** workflow from the Actions tab to build and push the production image. The workflow invokes `scripts/deployment/publish_image.sh` and pushes the `devsynth-api` image to the configured registry.

## Rollback

If a deployment fails, roll back to a known tag:

```bash
docker compose -f docker-compose.production.yml --profile ci run --rm rollback <previous_tag>
```

The `rollback` utility executes `scripts/deployment/rollback.sh` and validates service health via `scripts/deployment/health_check.sh`.

## Related Documents

- [Rollback Procedures](rollback.md)

## Tests

Run deployment tests after publishing or rolling back:

```bash
poetry run devsynth run-tests
```
