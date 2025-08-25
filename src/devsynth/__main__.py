# Defer heavy CLI imports until execution to keep import-time light and optional deps gated

if __name__ == "__main__":
    from devsynth.adapters.cli.typer_adapter import run_cli
    from devsynth.logging_setup import DevSynthLogger

    logger = DevSynthLogger(__name__)
    run_cli()
