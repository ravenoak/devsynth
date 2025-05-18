#!/usr/bin/env python3
"""
DevSynth CLI entry point.
"""
from devsynth.adapters.cli import run_cli

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError

if __name__ == "__main__":
    run_cli()
