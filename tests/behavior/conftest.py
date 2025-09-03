import contextlib
import os
from unittest import mock

import pytest

# Mark all behavior tests as requiring GUI by default. This ensures they are
# excluded from default collections per pytest.ini addopts: -m "not slow and not gui"
# Individual tests may override by removing or changing markers at the function level.
pytestmark = [pytest.mark.gui]


@pytest.fixture(autouse=True)
def enforce_offline_provider(monkeypatch: pytest.MonkeyPatch):
    """
    Ensure behavior tests avoid real network calls when DEVSYNTH_OFFLINE=true.

    Strategy:
    - Force provider factory paths to use a stub/safe provider if offline.
    - Common entry points are patched to avoid HTTP clients.
    - This fixture is autouse for all behavior tests.
    """
    offline = os.environ.get("DEVSYNTH_OFFLINE", "true").lower() in {"1", "true", "yes"}
    if not offline:
        # When explicitly online, do nothing; resource markers should gate execution.
        return

    # Prefer patching the unified provider factory to return a deterministic stub.
    patches = []

    # Patch provider factory used by application layer
    with contextlib.ExitStack() as stack:
        try:
            from devsynth.application.llm import provider_factory as pf  # type: ignore
        except Exception:
            pf = None  # pragma: no cover
        if pf is not None:
            # Patch choose_provider to always resolve to 'offline'/'stub' implementation
            if hasattr(pf, "choose_provider"):
                patches.append(
                    stack.enter_context(
                        mock.patch.object(
                            pf,
                            "choose_provider",
                            side_effect=lambda *_args, **_kw: "offline",
                        )
                    )
                )
            if hasattr(pf, "get_llm_provider"):
                # If there is a direct provider getter, force it to stub
                def _stub_provider(*_a, **_k):
                    try:
                        from devsynth.providers.stub import (
                            StubLLMProvider,  # type: ignore
                        )
                    except Exception:
                        # Fallback: a minimal object with expected interface
                        class _Minimal:
                            def chat(self, *args, **kwargs):
                                return {
                                    "choices": [{"message": {"content": "stubbed"}}]
                                }

                        return _Minimal()

                    return StubLLMProvider()

                patches.append(
                    stack.enter_context(
                        mock.patch.object(
                            pf, "get_llm_provider", side_effect=_stub_provider
                        )
                    )
                )

        # Additionally, harden the OpenAI/HTTP creation points to raise if reached offline
        try:
            from devsynth.application.llm import openai_provider as op  # type: ignore
        except Exception:
            op = None  # pragma: no cover
        if op is not None and hasattr(op, "OpenAI"):
            patches.append(
                stack.enter_context(
                    mock.patch.object(
                        op,
                        "OpenAI",
                        side_effect=RuntimeError(
                            "Network provider disabled in offline mode"
                        ),
                    )
                )
            )

        # Keep patches active during the test execution
        yield
        # Context stack will exit and remove patches
        return
