---
title: "MVU Report"
date: "2025-08-20"
version: "0.1.0a1"
tags:
  - "mvuu"
  - "user-guide"
  - "traceability"
status: "draft"
author: "DevSynth Team"
last_reviewed: "2025-08-20"
---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">User Guides</a> &gt; MVU Report
</div>

# MVU Report

The `mvu report` command scans git history for MVUU metadata and produces a
traceability matrix linking TraceIDs to files, tests, and issues.

## Usage

```bash
devsynth mvu report --since origin/main --format html --output report.html
```

### Options

- `--since`: Git revision to start scanning from. When omitted, the entire
  history reachable from `HEAD` is processed.
- `--format`: Output format, either `markdown` or `html` (default: `markdown`).
- `--output`: Destination file path. If omitted, the report is printed to
  standard output.

The generated matrix lists each TraceID alongside its utility statement,
affected files, tests, related issue, and the originating commit hash.
