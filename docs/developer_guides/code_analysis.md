---
author: DevSynth Team
date: '2025-07-12'
last_reviewed: '2025-07-12'
status: published
tags:
- developer-guide
- code-analysis
title: Code Analysis Guide
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; Code Analysis Guide
</div>

# Code Analysis Guide

DevSynth includes utilities for analyzing repository structure and transforming
code via Python's Abstract Syntax Tree (AST). This guide introduces the
`RepoAnalyzer`, the `AstTransformer`, and several built-in transformations.

## RepoAnalyzer

`RepoAnalyzer` walks a project directory, recording the folder hierarchy and
extracting top-level imports from Python files to map dependencies. The
`analyze` method returns a dictionary with separate `dependencies` and
`structure` keys, providing a lightweight overview of project composition.

## AstTransformer

`AstTransformer` offers programmatic code modifications using Python's AST. It
supports operations like renaming identifiers and extracting functions while
preserving valid syntax. The transformer logs initialization and each change for
traceability.

## Sample Transformations

DevSynth ships with several `AstTransformer` subclasses for common refactors:

- `UnusedImportRemover` drops imports that are never referenced.
- `RedundantAssignmentRemover` removes assignments whose values are immediately
  returned or self-assigned.
- `UnusedVariableRemover` strips variables that are declared but not used.
- `StringLiteralOptimizer` collapses string concatenations and trims excess
  whitespace.

These transformations can be combined through higher-level utilities to clean
entire files or directories.

## Related Specifications and Tests

- Specification: [DevSynth Post-MVP Testing Infrastructure](../specifications/testing_infrastructure.md).
- Unit tests: [`test_repo_analyzer.py`](../../tests/unit/application/code_analysis/test_repo_analyzer.py) and
  [`test_transformer.py`](../../tests/unit/application/code_analysis/test_transformer.py).

## Further Reading

See the [Technical Reference for AST Transformer](../technical_reference/ast_transformer.md)
for detailed API documentation.
