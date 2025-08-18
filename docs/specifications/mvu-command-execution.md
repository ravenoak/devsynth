---
author: DevSynth Team
date: 2025-02-19
last_reviewed: 2025-08-18
status: implemented
tags:
  - specification
  - mvu
  - command-execution
title: MVU Command Execution
version: 0.1.0-alpha.1
---

# Feature: MVU shell command execution

# Summary

The MVU command execution workflow dispatches MVU subcommands through the DevSynth CLI and reports their results.

## Socratic Checklist
- What is the problem?
- What proofs confirm the solution?

## Motivation

Developers need a dependable way to run MVU-specific commands and capture their outcomes for traceability.

## Specification

- A command `devsynth mvu exec <command>` runs `<command>` within the MVU context.
- The workflow captures both `stdout` and `stderr` and returns the combined output with the command's exit code.
- Failures propagate non-zero exit codes and the associated error output.

## Acceptance Criteria

- Executing `devsynth mvu exec echo hello` runs the shell command and outputs `hello`.
- The command exits with code `0` when the underlying command succeeds.
- Errors return a non-zero exit code and expose the underlying error message.
