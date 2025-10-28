"""Utilities and fixtures for optional test resources.

The helpers defined here centralize feature flags, Poetry extras messaging, and
optional backend imports so individual tests can share consistent skip
behaviour. They intentionally avoid importing optional dependencies until a test
requests them.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from collections.abc import Iterable, Mapping, Sequence
from importlib.machinery import ModuleSpec
from pathlib import Path
from typing import Any

import pytest

# Import is_resource_available from conftest to avoid circular import issues
try:
    from tests.conftest import is_resource_available
except ImportError:
    # Fallback for when conftest isn't fully loaded yet
    def is_resource_available(resource: str) -> bool:
        """Fallback implementation when conftest isn't available."""
        return False


try:  # pragma: no cover - optional dependency
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # type: ignore


BackendRequirement = Mapping[str, Sequence[str]]

OPTIONAL_BACKEND_REQUIREMENTS: dict[str, BackendRequirement] = {
    "chromadb": {
        "extras": ("chromadb", "memory"),
        "imports": ("chromadb",),
    },
    "faiss": {
        "extras": ("retrieval", "memory"),
        "imports": ("faiss",),
    },
    "kuzu": {
        "extras": ("retrieval", "memory"),
        "imports": ("kuzu",),
    },
    "lmdb": {
        "extras": ("memory", "tests"),
        "imports": ("lmdb",),
    },
    "vector": {
        "extras": ("memory", "tests"),
        "imports": ("numpy",),
    },
    "tinydb": {
        "extras": ("memory", "tests"),
        "imports": ("tinydb",),
    },
    "duckdb": {
        "extras": ("memory", "tests"),
        "imports": ("duckdb",),
    },
    "rdflib": {
        "extras": ("memory",),
        "imports": ("rdflib",),
    },
}


def resource_flag_enabled(resource: str) -> bool:
    """Return ``True`` when a resource flag explicitly enables the resource."""

    env_name = f"DEVSYNTH_RESOURCE_{resource.upper()}_AVAILABLE"
    value = os.environ.get(env_name, "").strip().lower()
    return value in {"1", "true", "yes"}


def _resolve_backend_metadata(
    resource: str,
    *,
    extras: Sequence[str] | None = None,
    import_names: Sequence[str] | None = None,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return normalized extras/imports for an optional backend resource."""

    meta = OPTIONAL_BACKEND_REQUIREMENTS.get(resource, {})
    resolved_extras: tuple[str, ...] = tuple(extras or meta.get("extras", ()) or ())
    resolved_imports: tuple[str, ...] = tuple(
        import_names or meta.get("imports", ()) or ()
    )
    return resolved_extras, resolved_imports


def _format_install_commands(extras: Iterable[str]) -> str:
    """Return a human-friendly installation hint for Poetry extras."""

    commands = [f"`poetry install --extras {extra}`" for extra in sorted(set(extras))]
    if not commands:
        return ""
    if len(commands) == 1:
        return commands[0]
    if len(commands) == 2:
        return " or ".join(commands)
    return ", ".join(commands[:-1]) + f", or {commands[-1]}"


def backend_skip_reason(resource: str, extras: Sequence[str]) -> str:
    """Generate a consistent skip message for optional backends."""

    env_name = f"DEVSYNTH_RESOURCE_{resource.upper()}_AVAILABLE"
    commands = _format_install_commands(extras)
    if commands:
        return (
            f"Optional backend '{resource}' unavailable. Install {commands} and ensure "
            f"{env_name}=true once dependencies are present."
        )
    return (
        f"Optional backend '{resource}' disabled or unavailable. Set {env_name}=true "
        "and install the required dependencies."
    )


def backend_import_reason(resource: str, extras: Sequence[str] | None = None) -> str:
    """Return a message for ``pytest.importorskip`` calls."""

    resolved_extras, _ = _resolve_backend_metadata(resource, extras=extras)
    commands = _format_install_commands(resolved_extras)
    if commands:
        return f"Install {commands} to enable the optional '{resource}' backend tests."
    return f"Optional backend '{resource}' dependencies are not installed."


def _safe_find_spec(name: str) -> ModuleSpec | None:
    """Return a module spec, tolerating environments with partial metadata."""

    try:
        spec = importlib.util.find_spec(name)
    except (ImportError, AttributeError, ValueError):
        return None
    return spec


def _spec_is_importable(spec: ModuleSpec | None) -> bool:
    """Return ``True`` when the provided spec represents an importable module."""

    if spec is None:
        return False
    loader = getattr(spec, "loader", None)
    submodule_locations = getattr(spec, "submodule_search_locations", ()) or ()
    if loader is None and not submodule_locations:
        return False
    if getattr(spec, "has_location", True) is False and not submodule_locations:
        return False
    origin = getattr(spec, "origin", None)
    if origin in {None, "namespace"} and not submodule_locations:
        # ``built-in`` origin with no loader/submodules indicates the spec is a
        # namespace stub emitted by importlib when the underlying module is absent.
        return False
    return True


def _importorskip_with_reason(
    module_name: str,
    *,
    import_reason: str,
    skip_reason: str,
) -> pytest.MarkDecorator | None:
    """Invoke :func:`pytest.importorskip`, returning a skip marker on failure."""

    try:
        pytest.importorskip(module_name, reason=import_reason)
    except pytest.skip.Exception as exc:  # pragma: no cover - exercised via tests
        message = getattr(exc, "msg", None) or skip_reason
        return pytest.mark.skip(reason=message)
    except Exception:
        return pytest.mark.skip(reason=skip_reason)
    return None


def skip_if_missing_backend(
    resource: str,
    *,
    extras: Sequence[str] | None = None,
    import_names: Sequence[str] | None = None,
    include_requires_resource: bool = True,
) -> list[pytest.MarkDecorator]:
    """Return markers ensuring optional backends skip cleanly when unavailable."""

    resolved_extras, resolved_imports = _resolve_backend_metadata(
        resource, extras=extras, import_names=import_names
    )
    markers: list[pytest.MarkDecorator] = []
    if include_requires_resource:
        markers.append(pytest.mark.requires_resource(resource))

    env_name = f"DEVSYNTH_RESOURCE_{resource.upper()}_AVAILABLE"
    if os.environ.get(env_name, "true").strip().lower() == "false":
        markers.append(
            pytest.mark.skip(
                reason=(
                    f"Optional backend '{resource}' disabled via {env_name}=false. "
                    "Enable the flag once dependencies are installed."
                )
            )
        )
        return markers

    skip_reason = backend_skip_reason(resource, resolved_extras)
    import_reason = backend_import_reason(resource, resolved_extras)

    for name in resolved_imports:
        module = sys.modules.get(name)
        if getattr(module, "__devsynth_optional_stub__", False):
            markers.append(pytest.mark.skip(reason=skip_reason))
            return markers

        spec = _safe_find_spec(name)
        if not _spec_is_importable(spec):
            if module is not None and getattr(module, "__spec__", None) is None:
                continue
            mark = _importorskip_with_reason(
                name, import_reason=import_reason, skip_reason=skip_reason
            )
            if mark is not None:
                markers.append(mark)
                return markers
            # Import succeeded; continue checking any remaining modules.

    if not is_resource_available(resource):
        markers.append(pytest.mark.skip(reason=skip_reason))

    return markers


def skip_module_if_backend_disabled(resource: str) -> None:
    """Skip module import when an optional backend is explicitly disabled."""

    env_name = f"DEVSYNTH_RESOURCE_{resource.upper()}_AVAILABLE"
    if os.environ.get(env_name, "true").strip().lower() == "false":
        pytest.skip(
            reason=(
                f"Optional backend '{resource}' disabled via {env_name}=false. "
                "Enable the flag once dependencies are installed."
            ),
            allow_module_level=True,
        )


def backend_param(
    *values,
    resource: str,
    extras: Sequence[str] | None = None,
    import_names: Sequence[str] | None = None,
    marks: Iterable[pytest.MarkDecorator] | None = None,
):
    """Convenience wrapper for parametrizing backend-dependent tests."""

    markers = list(marks or [])
    markers.extend(
        skip_if_missing_backend(
            resource,
            extras=extras,
            import_names=import_names,
            include_requires_resource=True,
        )
    )
    return pytest.param(*values, marks=markers)


@pytest.fixture(name="skip_if_missing_backend", scope="session")
def _skip_if_missing_backend_fixture():
    """Expose ``skip_if_missing_backend`` as a fixture for test functions."""

    return skip_if_missing_backend


@pytest.fixture(name="backend_param", scope="session")
def _backend_param_fixture():
    """Expose :func:`backend_param` for tests that prefer fixture injection."""

    return backend_param
