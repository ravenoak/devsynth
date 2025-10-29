---

author: DevSynth Team
date: '2025-07-10'
last_reviewed: '2025-07-10'
status: published
tags:

- policy
- audit
- dialogue

title: Dialectical Audit Policy
version: '0.1.0a1'
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Policies</a> &gt; Dialectical Audit Policy
</div>

# Dialectical Audit Policy

This policy defines how Socratic dialogues support audits that seek consensus between documentation, implementation, and tests.

## Preparation

- Use automated tools to surface inconsistencies among docs, code, and tests.
- Convert inconsistencies into open questions that challenge assumptions.

## Continuous Integration

- The dialectical audit script runs in continuous integration.
- The workflow may be triggered manually via GitHub's "Run workflow" dispatch for on-demand audits.
- The build fails if `dialectical_audit.log` contains unanswered questions.
- Release verification halts when `dialectical_audit.log` records unresolved questions.
- The log is archived as a workflow artifact for review.

## Dialogue Procedure

1. Present each question to all relevant contributors.
2. Record arguments, counterarguments, and supporting evidence.
3. Capture resolutions or actions for unresolved questions.

## Documentation

- Maintain a log of questions and resolutions in `dialectical_audit.log` produced by the audit script.
- Update docs, code, and tests to reflect agreed resolutions.
- Termination guarantees for evaluation hooks are detailed in the
  [Dialectical Reasoner Evaluation Hooks specification](../specifications/dialectical_reasoning.md#termination-proof)
  with accompanying [complexity analysis](../specifications/dialectical_reasoning.md#complexity-analysis).

## Review

- Include the audit log in code reviews and release discussions.
- Verify that all questions are resolved or tracked as issues before closing the audit.
