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

- **Coverage gate success (2025-10-12):** `poetry run devsynth run-tests --speed=fast --speed=medium --report --no-parallel` now completes with 92.40 % coverage (2,601/2,815 statements), archives HTML/JSON artifacts, and publishes knowledge-graph identifiers (`QualityGate=QG-20251012-FASTMED`, `TestRun=TR-20251012-FASTMED`, `ReleaseEvidence=RE-20251012-FASTMED`). The manifest records module-level coverage for `run_tests_cmd.py` (93.07 %) and `testing/run_tests.py` (91.48 %), demonstrating the uplift beyond the earlier 14 % baseline.【F:test_reports/coverage_manifest_20251012T164512Z.json†L1-L44】【F:artifacts/releases/0.1.0a1/fast-medium/20251012T164512Z-fast-medium/devsynth_run_tests_fast_medium_20251012T164512Z.txt†L1-L9】
- **Baseline failure reproduction:** Running `poetry run pytest -k "run_tests" --cov=src/devsynth/application/cli/commands/run_tests_cmd.py --cov=src/devsynth/testing/run_tests.py` still aborts during collection when optional extras such as `chromadb` are absent. Chunk `741149` mirrors the historical evidence recorded as chunk `24966b`, proving the aggregate suite cannot complete without installing dev extras or narrowing the scope.【741149†L1-L88】
- **History (focused sweep 2025-10-01):** Executing `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 poetry run pytest -p pytest_cov -p pytest_bdd.plugin --cov=devsynth.application.cli.commands.run_tests_cmd --cov=devsynth.testing.run_tests --cov-report=term --cov-report=json:test_reports/run-tests/coverage.json --cov-report=html:test_reports/run-tests/htmlcov --cov-fail-under=0 tests/unit/application/cli/commands/test_run_tests_cmd_cli_runner_invalid_inputs.py tests/unit/testing/test_run_tests_segmented_failures.py` recorded 18.32 % line coverage for `run_tests_cmd.py`, 11.93 % for `testing/run_tests.py`, and 14.26 % aggregate while generating JSON+HTML artifacts under `test_reports/run-tests/`.【cb4d4f†L1-L39】
- **Typer regression harness:** Minimal Typer apps now exercise invalid targets, speed flag validation, inventory exports, and maxfail remediation from within `CliRunner`, ensuring the command path surfaces actionable UX guidance without importing the entire CLI tree.【F:tests/unit/application/cli/commands/test_run_tests_cmd_cli_runner_invalid_inputs.py†L1-L337】
- **Segmented helper reinjection:** Unit tests for the orchestration helpers patch `collect_tests_with_cache` and `_run_single_test_batch` to force segmentation failures while verifying remediation hints, plugin reinjection, and aggregated logs.【F:tests/unit/testing/test_run_tests_segmented_failures.py†L1-L189】

## Regression Evidence

- `tests/unit/application/cli/commands/test_run_tests_cmd_inventory.py` confirms JSON export, exit codes, and coverage messaging for the inventory pathway under the current instrumentation defaults.【4a0778†L1-L19】
- Coverage artifacts for this run are versioned with the docs so future uplifts can quantify improvements in branches such as smoke mode, feature flags, provider defaults, and segmented execution.
- `tests/unit/application/cli/commands/test_help_rendering.py` guards the Rich panels, tables, and markdown surfaces used by CLI help so UX regressions surface immediately in targeted runs.【F:tests/unit/application/cli/commands/test_help_rendering.py†L1-L78】

## References

- Specification: [docs/specifications/devsynth-run-tests-command.md](../specifications/devsynth-run-tests-command.md)
- BDD Feature: [tests/behavior/features/devsynth_run_tests_command.feature](../tests/behavior/features/devsynth_run_tests_command.feature)
- Issue: [issues/run-tests-cli-invariants.md](../issues/run-tests-cli-invariants.md)
