---
title: "MVUU Configuration"
date: 2025-08-24
version: 0.1.0a1
status: active
last_reviewed: 2025-08-24
---

# MVUU Configuration

DevSynth stores configuration for the MVUU engine in `.devsynth/mvu.yml`.
This configuration controls where MVUU records (traceability entries) are stored
and which schema they follow.

- JSON Schema: docs/specifications/mvuu_config.schema.json
- MVUU Record Schema: docs/specifications/mvuuschema.json

## Example `.devsynth/mvu.yml`

```yaml
schema: "docs/specifications/mvuuschema.json"
storage:
  path: "docs/specifications/mvuu_database.json"
  format: "json"
issues:
  github:
    base_url: "https://api.github.com/repos/ORG/REPO"
    token: "YOUR_GITHUB_TOKEN"
  jira:
    base_url: "https://jira.example.com"
    token: "YOUR_JIRA_TOKEN"
```

Notes:
- The `schema` field references the schema that validates MVUU records embedded in
  commit messages and stored in your database file.
- The `storage` configuration defines the database location and format.
- Issue provider settings are optional, used by integrations that query external
  systems for additional metadata.
