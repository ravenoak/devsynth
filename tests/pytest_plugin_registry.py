"""Unified registry for pytest plugins used across DevSynth test suites."""

from __future__ import annotations

from importlib import import_module
from typing import Iterable, Iterator, Sequence

__all__ = ["PYTEST_PLUGINS", "iter_pytest_plugins"]

# Core plugins explicitly required by the test suite.
# pytest>=8 removed implicit plugin discovery from non-root modules, so we
# register ``pytest_bdd.plugin`` here to guarantee the behavior steps collect
# without relying on scattered ``pytest_plugins`` declarations.
_CORE_PLUGINS: tuple[str, ...] = ("pytest_bdd.plugin",)

# Legacy helper modules that may still expose ``pytest_plugins`` declarations.
# Loading them here lets us hoist their entries into the root registry without
# keeping duplicate definitions scattered across the test tree.
_LEGACY_PLUGIN_EXPORTERS: tuple[str, ...] = ()


def _load_plugins_from(module_name: str) -> Iterable[str]:
    """Load plugin names from a legacy helper module, if available."""

    try:
        module = import_module(module_name)
    except Exception:
        return ()
    plugins = getattr(module, "PYTEST_PLUGINS", None)
    if not plugins:
        plugins = getattr(module, "pytest_plugins", ())
    return tuple(plugins)


def _deduplicate(names: Sequence[str]) -> tuple[str, ...]:
    """Return names in ``names`` preserving order while removing duplicates."""

    seen: list[str] = []
    for name in names:
        if name not in seen:
            seen.append(name)
    return tuple(seen)


PYTEST_PLUGINS: tuple[str, ...] = _deduplicate(
    [
        *_CORE_PLUGINS,
        *(
            plugin
            for exporter in _LEGACY_PLUGIN_EXPORTERS
            for plugin in _load_plugins_from(exporter)
        ),
    ]
)


def iter_pytest_plugins() -> Iterator[str]:
    """Iterate over registered pytest plugin entry points."""

    yield from PYTEST_PLUGINS
