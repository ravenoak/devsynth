---
title: "Atomic Rewrite Tutorial"
date: "2025-08-20"
version: "0.1.0-alpha.1"
tags:
  - "mvu"
  - "user-guide"
status: "draft"
author: "DevSynth Team"
last_reviewed: "2025-08-20"
---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">User Guides</a> &gt; Atomic Rewrite Tutorial
</div>

# Atomic Rewrite Tutorial

The atomic rewrite utility restructures a repository's commit history so that
each commit touches a single file. This can make code review and traceability
clearer.

## Usage

```bash
devsynth mvu rewrite --path PATH_TO_REPO --branch-name atomic
```

Use `--dry-run` to preview the operation without creating commits.

The rewritten history is placed on the branch specified by `--branch-name`.
