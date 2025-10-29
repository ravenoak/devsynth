---
title: "MVU Initialization"
date: "2025-08-20"
version: "0.1.0a1"
tags:
  - "mvuu"
  - "configuration"
status: "draft"
author: "DevSynth Team"
last_reviewed: "2025-08-20"
---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">User Guides</a> &gt; MVU Initialization
</div>

# MVU Initialization

Use `devsynth mvu init` to create the `.devsynth/mvu.yml` configuration file. The generated file now includes optional settings for issue tracking integrations:

```yaml
schema: docs/specifications/mvuuschema.json
storage:
  path: docs/specifications/mvuu_database.json
  format: json
issues:
  github:
    base_url: https://api.github.com/repos/ORG/REPO
    token: YOUR_GITHUB_TOKEN
  jira:
    base_url: https://jira.example.com
    token: YOUR_JIRA_TOKEN
```

Populate the placeholders with the correct API endpoints and tokens for your project. When configured, MVU utilities can fetch ticket titles and acceptance criteria from GitHub or Jira when a commit's `TraceID` references an external ticket.
