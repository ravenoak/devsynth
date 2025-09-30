# Focused Coverage — Long-running Progress Indicator

- **Command:** `poetry run pytest tests/unit/application/cli/test_long_running_progress.py -k "simulation_timeline" --maxfail=1`
- **Modules:** `src/devsynth/application/cli/long_running_progress.py`
- **Highlights:** deterministic `simulate_progress_timeline` flow covers nested subtasks, ETA checkpoints, and completion banners under a fake Rich progress implementation.
