# Lazy attribute access to avoid import-time side effects and module shadowing.
# This preserves both usage patterns:
# - from devsynth.methodology.edrr import reasoning_loop  -> returns callable
# - import devsynth.methodology.edrr.reasoning_loop as rl -> returns submodule

__all__: list[str] = [
    "EDRRCoordinator",
    "reasoning_loop",
    "MemoryIntegration",
    "MemoryManager",
    "EDRRCoordinatorProtocol",
    "WSDETeamProtocol",
    "NullWSDETeam",
    "CoordinatorRecorder",
    "MemoryIntegrationLog",
]


def __getattr__(name: str) -> object:  # PEP 562
    if name == "EDRRCoordinator":
        from .coordinator import EDRRCoordinator as _EDRRCoordinator

        return _EDRRCoordinator
    if name == "reasoning_loop":
        from .reasoning_loop import reasoning_loop as _reasoning_loop

        return _reasoning_loop
    contract_names = {
        "MemoryIntegration",
        "MemoryManager",
        "EDRRCoordinatorProtocol",
        "WSDETeamProtocol",
        "NullWSDETeam",
        "CoordinatorRecorder",
        "MemoryIntegrationLog",
    }
    if name in contract_names:
        from . import contracts as _contracts

        return getattr(_contracts, name)
    raise AttributeError(name)
