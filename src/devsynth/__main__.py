# Defer heavy CLI imports; avoid importing optional deps at module import time

if __name__ == "__main__":
    from devsynth.adapters.cli.typer_adapter import run_cli
    from devsynth.logging_setup import DevSynthLogger

    logger = DevSynthLogger(__name__)
    run_cli()
