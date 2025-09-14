from .adhoc import AdHocAdapter
from .edrr import reasoning_loop
from .kanban import KanbanAdapter
from .milestone import MilestoneAdapter
from .sprint import SprintAdapter

__all__ = [
    "AdHocAdapter",
    "SprintAdapter",
    "KanbanAdapter",
    "MilestoneAdapter",
    "reasoning_loop",
]

# Provide attribute access to the edrr submodule for tools that resolve via getattr
# (e.g., pytest monkeypatch path resolution): devsynth.methodology.edrr


from typing import Any


def __getattr__(name: str) -> Any:  # PEP 562
    if name == "edrr":
        import importlib as _importlib

        return _importlib.import_module(__name__ + ".edrr")
    raise AttributeError(name)
