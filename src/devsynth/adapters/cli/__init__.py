"""CLI adapter exports."""

from devsynth.logging_setup import DevSynthLogger

from .typer_adapter import app, run_cli

logger = DevSynthLogger(__name__)
