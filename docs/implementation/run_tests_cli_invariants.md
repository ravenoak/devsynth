---
author: DevSynth Team
date: '2025-09-13'
status: draft
tags:
- implementation
- invariants
title: Run Tests CLI Invariants
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Implementation</a> &gt; Run Tests CLI Invariants
</div>

# Run Tests CLI Invariants

This note captures invariants of the `devsynth run-tests` CLI and demonstrates them via small simulations.

## Option Normalization

The CLI converts `--feature` flags into deterministic environment variables.

```python
from devsynth.application.cli.commands.run_tests_cmd import _parse_feature_options

assert _parse_feature_options(["demo", "trace=false"]) == {"demo": True, "trace": False}
```

## Inventory Mode is Side Effect Free

When invoked with `--inventory` the command writes a JSON report and exits without running tests.

```python
from pathlib import Path
from devsynth.application.cli.commands.run_tests_cmd import run_tests_cmd
import json, os

# ensure clean state
Path("test_reports").mkdir(exist_ok=True)
Path("test_reports/test_inventory.json").unlink(missing_ok=True)

run_tests_cmd(target="unit-tests", speeds=["fast"], inventory=True)

data = json.loads(Path("test_reports/test_inventory.json").read_text())
assert "tests/unit" in data["tests"][0]["nodeid"]
```

## References

- Specification: [docs/specifications/devsynth-run-tests-command.md](../specifications/devsynth-run-tests-command.md)
- BDD Feature: [tests/behavior/features/devsynth_run_tests_command.feature](../tests/behavior/features/devsynth_run_tests_command.feature)
- Issue: [issues/run-tests-cli-invariants.md](../issues/run-tests-cli-invariants.md)
