---
title: "Release Automation"
date: "2025-08-23"
version: "0.1.0-alpha.1"
tags:
  - "release"
  - "automation"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-08-23"
---

# Release Automation

DevSynth uses scripted steps to prepare and tag each release.

## Artifact Generation

Generate distribution and documentation artifacts:

```bash
poetry run task release:prep
```

## Audit

Produce a dialectical audit log and resolve any findings:

```bash
poetry run python scripts/dialectical_audit.py
```

## Tagging

Create an annotated tag after the artifacts and audit complete:

```bash
git tag -a vX.Y.Z -m "DevSynth vX.Y.Z"
git push origin vX.Y.Z
```

These steps ensure every release includes generated artifacts, a recorded audit, and a signed tag.
