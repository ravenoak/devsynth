---
author: DevSynth Team
date: '2025-09-17'
status: published
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

## Coverage Instrumentation Guarantees (2025-09-17)

- **Focused regression sweep:** `poetry run coverage run -m pytest --override-ini addopts="" tests/unit/application/cli/commands/test_run_tests_cmd_inventory.py` exercises the Typer command through the inventory pathway, persisting artifacts at `test_reports/run_tests_cmd_coverage.json` and `test_reports/htmlcov_run_tests_cmd/index.html` to capture the coverage gate wiring.【4a0778†L1-L19】
- **Measured coverage:** The sweep covers 58 of 177 statements (32.77 % line coverage) in `src/devsynth/application/cli/commands/run_tests_cmd.py`, highlighting that inventory/export logic is validated while other option paths still require additional tests.【7e4fe3†L1-L9】
- **Instrumentation contract:** The command aborts with actionable remediation when coverage plugins are disabled or artifacts are missing, ensuring maintainers cannot silently bypass the ≥90 % gate without acknowledging the condition.【F:src/devsynth/application/cli/commands/run_tests_cmd.py†L300-L433】

## Regression Evidence

- `tests/unit/application/cli/commands/test_run_tests_cmd_inventory.py` confirms JSON export, exit codes, and coverage messaging for the inventory pathway under the current instrumentation defaults.【4a0778†L1-L19】
- Coverage artifacts for this run are versioned with the docs so future uplifts can quantify improvements in branches such as smoke mode, feature flags, provider defaults, and segmented execution.

## References

- Specification: [docs/specifications/devsynth-run-tests-command.md](../specifications/devsynth-run-tests-command.md)
- BDD Feature: [tests/behavior/features/devsynth_run_tests_command.feature](../tests/behavior/features/devsynth_run_tests_command.feature)
- Issue: [issues/run-tests-cli-invariants.md](../issues/run-tests-cli-invariants.md)
