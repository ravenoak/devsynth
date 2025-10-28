"""Unified registry for pytest plugins used across DevSynth test suites."""

from __future__ import annotations

import os
from importlib import import_module
from importlib.util import find_spec
from collections.abc import Iterable, Iterator, Sequence

__all__ = ["PYTEST_PLUGINS", "iter_pytest_plugins"]

# Core plugins explicitly required by the test suite. Items in
# ``_OPTIONAL_CORE_PLUGINS`` are only included when their modules can be
# imported to avoid triggering ImportError during collection on fresh
# environments where optional extras are absent.
_CORE_PLUGINS: tuple[str, ...] = ()
_OPTIONAL_CORE_PLUGINS: tuple[str, ...] = ("pytest_bdd.plugin",)

# Legacy helper modules that may still expose ``pytest_plugins`` declarations.
# Loading them here lets us hoist their entries into the root registry without
# keeping duplicate definitions scattered across the test tree.
_LEGACY_PLUGIN_EXPORTERS: tuple[str, ...] = ()


def _is_importable(plugin_name: str) -> bool:
    """Return ``True`` when the module portion of ``plugin_name`` is importable."""

    module_name, _, _ = plugin_name.partition(":")
    return find_spec(module_name) is not None


def _autoload_disabled() -> bool:
    """Return ``True`` when pytest's plugin autoloading is disabled."""

    value = os.environ.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD")
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes"}


def _resolve_optional_plugins(names: Sequence[str]) -> Iterable[str]:
    """Yield plugin names from ``names`` when autoloading is disabled."""

    if not _autoload_disabled():
        return ()
    for name in names:
        if _is_importable(name):
            yield name


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
        *(_resolve_optional_plugins(_OPTIONAL_CORE_PLUGINS)),
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
