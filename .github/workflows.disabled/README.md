# Disabled Workflows

These workflow templates run core project checks before executing their primary tasks. Each workflow executes:

- `python scripts/run_all_tests.py`
- `python scripts/check_internal_links.py`
- `python scripts/fix_code_blocks.py --check`

The job fails if any of these scripts report errors.
