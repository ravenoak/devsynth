"""Runtime compatibility patches applied at interpreter startup."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
import types
from pathlib import Path
from typing import Any, Dict


def _patch_starlette_testclient() -> None:
    """Patch Starlette's TestClient to avoid Python 3.12 MRO conflicts."""

    sys.modules.pop("starlette.testclient", None)

    try:
        spec = importlib.util.find_spec("starlette.testclient")
    except ModuleNotFoundError:
        return
    if not spec or not isinstance(spec.loader, importlib.machinery.SourceFileLoader):
        return

    origin = spec.origin
    if origin is None:
        return

    source_path = Path(origin)
    try:
        source = source_path.read_text()
    except OSError:
        return

    original_header = (
        "class WebSocketDenialResponse(  # type: ignore[misc]\n"
        "    httpx.Response,\n"
        "    WebSocketDisconnect,\n"
        '):\n    """'
    )
    if original_header not in source:
        return

    try:
        import httpx
        from starlette.websockets import WebSocketDisconnect
    except Exception:
        return

    replacement = (
        "class WebSocketDenialResponse(WebSocketDisconnect):\n"
        '    """Patched fallback to avoid Python 3.12 MRO conflicts between\n'
        '    httpx.Response and WebSocketDisconnect."""\n\n'
        "    def __init__(self, *args, **kwargs):\n"
        "        self._response = httpx.Response(*args, **kwargs)\n"
        "        code = kwargs.get('status_code', self._response.status_code)\n"
        "        reason = kwargs.get('reason', None)\n"
        "        super().__init__(code=code, reason=reason)\n\n"
        "    def __getattr__(self, name):\n"
        "        return getattr(self._response, name)\n\n"
        "    def __iter__(self):\n"
        "        return iter(self._response)\n"
    )

    patched_source = source.replace(original_header, replacement)
    module = types.ModuleType("starlette.testclient")
    module.__file__ = str(source_path)
    module.__package__ = "starlette"
    module.__spec__ = importlib.util.spec_from_loader(
        "starlette.testclient", spec.loader
    )

    exec_globals: dict[str, Any] = module.__dict__
    exec_globals["httpx"] = httpx
    exec_globals["WebSocketDisconnect"] = WebSocketDisconnect

    try:
        exec(patched_source, exec_globals)
    except SyntaxError:
        # If Starlette's source layout changes, skip patching instead of aborting startup
        return
    sys.modules["starlette.testclient"] = module


_patch_starlette_testclient()
