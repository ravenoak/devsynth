---
title: "Semantic Versioning Policy"
date: "2025-07-07"
version: "0.1.0"
tags:
  - "policy"
  - "versioning"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-07-10"
---

# Semantic Versioning Policy

DevSynth follows the [Semantic Versioning](https://semver.org/) scheme to communicate changes and compatibility.

## Version Components

- **MAJOR** version when incompatible API changes are introduced.
- **MINOR** version when functionality is added in a backward compatible manner.
- **PATCH** version for backward compatible bug fixes.

## Pre-release Identifiers

Pre-release versions append an identifier after a hyphen (e.g., `1.2.0-alpha`, `2.0.0-rc.1`) to denote milestones that precede a final release.

## MAJOR.MINOR.PATCH-STABILITY

DevSynth uses an extended scheme that appends a stability label after the patch
component. The general form is `MAJOR.MINOR.PATCH-STABILITY`.

- **STABILITY** indicates the maturity of the release. Typical values are
  `alpha`, `beta`, and `rc` followed by a dot and an incrementing number.
- Final releases omit the stability label entirely.

### Examples

- `0.1.0-alpha.1` – first alpha iteration of version `0.1.0`.
- `0.1.0-beta.2` – second beta iteration of version `0.1.0`.
