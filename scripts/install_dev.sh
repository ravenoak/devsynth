#!/usr/bin/env bash
set -euo pipefail

# Install DevSynth with development and documentation dependencies and required extras
poetry install --with dev,docs --extras "tests retrieval chromadb api"

# Install pre-commit hooks to enable repository checks
poetry run pre-commit install --install-hooks
