#!/usr/bin/env bash
set -euo pipefail

# Install DevSynth with development and documentation dependencies and required extras
poetry install --with dev,docs --extras "tests retrieval chromadb api"
