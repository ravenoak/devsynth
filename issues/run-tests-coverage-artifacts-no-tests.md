Title: run-tests missing coverage artifacts when no tests collected
Date: 2025-09-16 00:00 UTC
Status: closed
Affected Area: testing
Reproduction:
  - `poetry run devsynth run-tests --speed=fast --speed=medium --report --no-parallel`
Resolution: ensure htmlcov/ and coverage.json are generated even when no tests run.
