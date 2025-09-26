---
author: DevSynth Team
date: '2025-09-20'
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

## Failure-Path Regression Proofs (2025-09-24)

- **Baseline failure reproduction:** Running `poetry run pytest -k "run_tests" --cov=src/devsynth/application/cli/commands/run_tests_cmd.py --cov=src/devsynth/testing/run_tests.py` still aborts during collection when optional extras such as `chromadb` are absent. Chunk `741149` mirrors the historical evidence recorded as chunk `24966b`, proving the aggregate suite cannot complete without installing dev extras or narrowing the scope.【741149†L1-L88】
- **Targeted coverage sweep:** Constraining the run to the CLI regression suites keeps pytest focused on the new invariants: `poetry run pytest -o addopts="" tests/unit/application/cli/commands/test_run_tests_cmd_cli_runner_paths.py tests/unit/application/cli/commands/test_run_tests_cmd_coverage_artifacts.py --cov=devsynth.application.cli.commands.run_tests_cmd --cov=devsynth.testing.run_tests --cov-report=term-missing --cov-fail-under=0`. Chunk `834bbe` records a 45.5 % line rate for `run_tests_cmd.py`, 52.8 % for `testing/run_tests.py`, and a 14.7 % aggregate while still producing JSON+HTML artifacts for inspection.【834bbe†L1-L275】
- **Typer regression harness:** Minimal Typer apps now exercise segmentation failure tips, plugin reinjection, inventory JSON emission, and coverage gating through dedicated fast tests so the CLI behavior is validated without importing the entire command tree.【F:tests/unit/application/cli/commands/test_run_tests_cmd_cli_runner_paths.py†L1-L200】【F:tests/unit/application/cli/commands/test_run_tests_cmd_coverage_artifacts.py†L1-L385】
- **Failure-path CLI assertions:** `test_failed_run_surfaces_maxfail_guidance` now exercises Typer’s maxfail propagation to guarantee remediation tips surface when segmented runs exit non-zero, closing the regression noted in the baseline failure log.【F:tests/unit/application/cli/commands/test_run_tests_cmd.py†L403-L443】 Inventory mode likewise tolerates collection crashes by exporting empty lists instead of blowing up the command, ensuring operators can still capture the remaining targets.【F:tests/unit/application/cli/commands/test_run_tests_cmd_inventory_and_validation.py†L72-L102】
- **Segmented helper reinjection:** Focused helper tests assert that segmented batches re-hydrate pytest-cov and pytest-bdd even when `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, and that troubleshooting banners only appear once per batch/aggregate. The `_assert_plugins_in_addopts`/`_assert_plugins_in_env` utilities make plugin reinjection explicit while documenting the environment mutations under segmentation failures.【F:tests/unit/testing/test_run_tests_cli_helpers_focus.py†L23-L177】

## Regression Evidence

- `tests/unit/application/cli/commands/test_run_tests_cmd_inventory.py` confirms JSON export, exit codes, and coverage messaging for the inventory pathway under the current instrumentation defaults.【4a0778†L1-L19】
- Coverage artifacts for this run are versioned with the docs so future uplifts can quantify improvements in branches such as smoke mode, feature flags, provider defaults, and segmented execution.

## References

- Specification: [docs/specifications/devsynth-run-tests-command.md](../specifications/devsynth-run-tests-command.md)
- BDD Feature: [tests/behavior/features/devsynth_run_tests_command.feature](../tests/behavior/features/devsynth_run_tests_command.feature)
- Issue: [issues/run-tests-cli-invariants.md](../issues/run-tests-cli-invariants.md)
