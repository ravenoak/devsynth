"""
Unified stubbing utilities for GUI and provider subsystems used in tests.

Rationale:
- Normalizes mocking/stubbing across GUI/provider subsystems (docs/tasks.md item 14).
- Prevents real network/UI interactions during tests while allowing explicit opt-out.
- Keeps deterministic, fast, and hermetic test runs aligned with .junie/guidelines.md.

Usage:
- Imported and applied by tests/conftest.py via an autouse fixture.
- Opt-out by setting environment variables before running tests:
  - DEVSYNTH_TEST_ALLOW_GUI=true  -> do not stub GUI modules
  - DEVSYNTH_TEST_ALLOW_PROVIDERS=true -> do not stub LLM provider classes
"""

from __future__ import annotations

import os
import sys
from types import ModuleType
from unittest.mock import MagicMock


def _install_module_stub(module_name: str, attrs: dict | None = None) -> ModuleType:
    """Create and insert a stub module into sys.modules with optional attributes.

    This makes `import module_name` succeed even if the real module is not installed.
    """
    mod = ModuleType(module_name)
    if attrs:
        for k, v in attrs.items():
            setattr(mod, k, v)
    sys.modules[module_name] = mod
    return mod


def stub_gui_modules() -> None:
    """Stub NiceGUI and DearPyGui modules to avoid optional GUI deps during tests.

    Creates minimal, no-op APIs where necessary.
    """
    # NiceGUI stubs
    if "nicegui" not in sys.modules:
        _install_module_stub("nicegui", attrs={"ui": MagicMock(name="nicegui.ui")})
    # Common nested imports used by apps
    if "nicegui.app" not in sys.modules:
        _install_module_stub("nicegui.app", attrs={})

    # DearPyGui stubs (some code imports as `from dearpygui import dearpygui as dpg`)
    if "dearpygui" not in sys.modules:
        _install_module_stub("dearpygui", attrs={})
    if "dearpygui.dearpygui" not in sys.modules:
        dpg_stub = MagicMock(name="dearpygui.dearpygui")
        dpg_stub.configure_app = MagicMock()
        dpg_stub.create_context = MagicMock()
        dpg_stub.destroy_context = MagicMock()
        dpg_stub.create_viewport = MagicMock()
        dpg_stub.setup_dearpygui = MagicMock()
        dpg_stub.show_viewport = MagicMock()
        dpg_stub.start_dearpygui = MagicMock()
        dpg_stub.set_primary_window = MagicMock()
        dpg_stub.add_text = MagicMock()
        _install_module_stub("dearpygui.dearpygui", attrs=dpg_stub.__dict__)


def stub_providers() -> None:
    """Stub provider classes across both adapters and application layers.

    Provides deterministic return values for `complete` and `embed` methods.
    """
    # Adapter-layer providers
    try:
        import devsynth.adapters.provider_system as adapter_ps  # type: ignore

        class _ProviderStub:
            def __init__(self, *_, **__):
                pass

            def complete(self, *_, **__):
                return "Test completion response"

            def embed(self, *_, **__):
                return [0.1, 0.2, 0.3, 0.4]

        if hasattr(adapter_ps, "OpenAIProvider"):
            adapter_ps.OpenAIProvider = _ProviderStub  # type: ignore[attr-defined]
        if hasattr(adapter_ps, "LMStudioProvider"):
            adapter_ps.LMStudioProvider = _ProviderStub  # type: ignore[attr-defined]
        if hasattr(adapter_ps, "AnthropicProvider"):
            adapter_ps.AnthropicProvider = _ProviderStub  # type: ignore[attr-defined]
    except Exception:
        # If import fails, tests using adapters should import the stub via patching elsewhere
        pass

    # Application-layer OpenAI provider: opt-in stubbing only.
    # Some unit tests assert internal behaviors of the real provider (e.g., constructor patching),
    # so we avoid overriding it by default. Enable via DEVSYNTH_TEST_STUB_APP_OPENAI=true when desired.
    if os.getenv("DEVSYNTH_TEST_STUB_APP_OPENAI", "false").lower() in {
        "1",
        "true",
        "yes",
    }:
        try:
            import devsynth.application.llm.openai_provider as app_openai  # type: ignore

            class _AppOpenAIStub:
                def __init__(self, *_, **__):
                    pass

                def complete(self, *_, **__):
                    return "Test completion response"

                def embed(self, *_, **__):
                    return [0.1, 0.2, 0.3, 0.4]

            if hasattr(app_openai, "OpenAIProvider"):
                app_openai.OpenAIProvider = _AppOpenAIStub  # type: ignore[attr-defined]
        except Exception:
            pass

    # Optional stub for application-layer LMStudio provider.
    # Disabled by default to allow tests to patch internals of the real provider class.
    if os.getenv("DEVSYNTH_TEST_STUB_APP_LMSTUDIO", "false").lower() in {
        "1",
        "true",
        "yes",
    }:
        try:
            import devsynth.application.llm.lmstudio_provider as app_lms  # type: ignore

            # Only stub LMStudio when the resource is not explicitly enabled.
            _lmstudio_resource_enabled = os.getenv(
                "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "false"
            ).lower() in {"1", "true", "yes"}

            if not _lmstudio_resource_enabled:

                class _AppLMStudioStub:
                    def __init__(self, *_, **__):
                        pass

                    # Application-layer API shape
                    def generate(self, *_, **__):
                        return "Test completion response"

                    def generate_with_context(self, *_, **__):
                        return "Test completion response"

                    def get_embedding(self, *_, **__):
                        return [0.1, 0.2, 0.3, 0.4]

                    # Adapter-style methods for compatibility (some tests call these)
                    def complete(self, *_, **__):
                        return "Test completion response"

                    def embed(self, *_, **__):
                        return [0.1, 0.2, 0.3, 0.4]

                if hasattr(app_lms, "LMStudioProvider"):
                    app_lms.LMStudioProvider = _AppLMStudioStub  # type: ignore[attr-defined]
        except Exception:
            pass


def apply_normalized_stubs() -> None:
    """Apply normalized stubs for GUI and providers based on env toggles.

    - Stubs are applied by default to maximize test hermeticity.
    - Set DEVSYNTH_TEST_ALLOW_GUI=true to keep real GUI modules (if installed).
    - Set DEVSYNTH_TEST_ALLOW_PROVIDERS=true to keep real provider classes.
    """
    allow_gui = os.getenv("DEVSYNTH_TEST_ALLOW_GUI", "false").lower() in {
        "1",
        "true",
        "yes",
    }
    allow_providers = os.getenv("DEVSYNTH_TEST_ALLOW_PROVIDERS", "false").lower() in {
        "1",
        "true",
        "yes",
    }

    if not allow_gui:
        stub_gui_modules()
    if not allow_providers:
        stub_providers()
