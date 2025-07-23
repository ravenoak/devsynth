
"""Behavior test step definitions package."""

from __future__ import annotations

import importlib
import pkgutil
import sys

# Automatically provide modules without the ``test_`` prefix used on disk.
for _finder, _name, _ispkg in pkgutil.iter_modules(__path__):
    if _name.startswith("test_"):
        _alias = _name[5:]
        _module = importlib.import_module(f".{_name}", __name__)
        sys.modules[f"{__name__}.{_alias}"] = _module
