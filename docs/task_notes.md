2025-09-08:
- Environment lacked `task`; ran scripts/install_dev.sh to install v3.44.1.
- Executed `poetry install --with dev --extras "tests retrieval chromadb api"` to fix missing `devsynth` module.
- Restored missing sentinel test `tests/test_speed_dummy.py` to satisfy organization checks.
- Fast tests now pass; verify scripts succeed.
- Outstanding: validate medium/slow tests and resolve pytest-xdist errors.
