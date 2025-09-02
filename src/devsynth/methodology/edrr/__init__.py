# Lazy attribute access to avoid import-time side effects and module shadowing.
# This preserves both usage patterns:
# - from devsynth.methodology.edrr import reasoning_loop  -> returns callable
# - import devsynth.methodology.edrr.reasoning_loop as rl -> returns submodule

__all__ = ["EDRRCoordinator", "reasoning_loop"]

def __getattr__(name: str):  # PEP 562
    if name == "EDRRCoordinator":
        from .coordinator import EDRRCoordinator as _EDRRCoordinator

        return _EDRRCoordinator
    if name == "reasoning_loop":
        from .reasoning_loop import reasoning_loop as _reasoning_loop

        return _reasoning_loop
    raise AttributeError(name)
