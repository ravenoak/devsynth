#!/usr/bin/env python3
"""DevSynth CLI entry point."""

from devsynth.adapters.cli.argparse_adapter import run_cli
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)

if __name__ == "__main__":
    run_cli()
