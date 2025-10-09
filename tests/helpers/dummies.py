"""Lightweight dummy implementations for testing.

These classes provide minimal behavior to satisfy interfaces without
performing any external calls.  They exist to keep tests fast and
offline-friendly.
"""

from __future__ import annotations

from devsynth.domain.models.wsde_facade import WSDETeam


class _DummyTeam(WSDETeam):
    """Simplified team for property tests.

    Implements the private hooks expected by ``apply_dialectical_reasoning``
    with trivial semantics so that property tests can exercise the public
    API without relying on network or heavy dependencies.
    """

    def __init__(self) -> None:
        super().__init__(name="TestTeam")

    # Minimal implementations satisfy the interface but avoid extra work.
    def _improve_clarity(self, content: str) -> str:  # pragma: no cover - trivial
        return content.strip()

    def _improve_with_examples(self, content: str) -> str:  # pragma: no cover - trivial
        return content

    def _check_pep8_compliance(self, code: str) -> dict:  # pragma: no cover - trivial
        return {"compliance_level": "high", "issues": [], "suggestions": []}

    def _check_security_best_practices(
        self, code: str
    ) -> dict:  # pragma: no cover - trivial
        return {"compliance_level": "high", "issues": [], "suggestions": []}


class DummySessionState(dict):
    """Dictionary-backed session state supporting attribute access."""

    def __getattr__(self, item: str):
        try:
            return self[item]
        except KeyError as exc:  # pragma: no cover - defensive
            raise AttributeError(item) from exc

    def __setattr__(self, key: str, value) -> None:
        self[key] = value


class DummySidebar:
    """Minimal sidebar stub capturing title and markdown invocations."""

    def __init__(self) -> None:
        self.titles: list[str] = []
        self.markdowns: list[tuple[str, dict]] = []

    def title(self, text: str) -> None:
        self.titles.append(text)

    def markdown(self, text: str, **kwargs) -> None:
        self.markdowns.append((text, kwargs))

    def radio(self, _label: str, options: list[str], *, index: int = 0):
        return options[index]


class DummyStreamlit:
    """Lightweight Streamlit replacement for deterministic tests."""

    def __init__(self) -> None:
        from types import SimpleNamespace

        self.set_page_config_calls: list[dict] = []
        self.markdown_calls: list[tuple[str, dict]] = []
        self.writes: list[tuple[tuple, dict]] = []
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.successes: list[str] = []
        self.infos: list[str] = []
        self.checkbox_defaults: dict[str, bool] = {}
        self.text_inputs: dict[str, str] = {}
        self.selectboxes: dict[str, tuple[str, list[str], int]] = {}
        self.session_state = DummySessionState()
        self.sidebar = DummySidebar()
        self.components = SimpleNamespace(v1=SimpleNamespace(html=lambda *a, **k: None))

    def set_page_config(self, **kwargs) -> None:
        self.set_page_config_calls.append(kwargs)

    def markdown(self, text: str, **kwargs) -> None:
        self.markdown_calls.append((text, kwargs))

    def write(self, *args, **kwargs) -> None:
        self.writes.append((args, kwargs))

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)

    def success(self, message: str) -> None:
        self.successes.append(message)

    def info(self, message: str) -> None:
        self.infos.append(message)

    def checkbox(
        self, label: str, *, value: bool = False, key: str | None = None
    ) -> bool:
        key = key or label
        self.checkbox_defaults[key] = value
        return value

    def text_input(self, label: str, *, value: str = "", key: str | None = None) -> str:
        key = key or label
        self.text_inputs[key] = value
        return value

    def selectbox(
        self,
        label: str,
        options: list[str],
        *,
        index: int = 0,
        key: str | None = None,
    ) -> str:
        key = key or label
        self.selectboxes[key] = (label, options, index)
        return options[index]


class DummyWizardManager:
    """Capture hydration inputs from ``WebUIBridge`` helpers."""

    def __init__(
        self,
        session_state: DummySessionState,
        wizard_name: str,
        steps: int,
        initial_state: dict | None = None,
    ) -> None:
        self.session_state = session_state
        self.wizard_name = wizard_name
        self.steps = steps
        self.initial_state = initial_state or {}
        self._state = {"current_step": 0, **self.initial_state}

    def get_wizard_state(self) -> dict:
        return self._state


class DummyProvider:
    """Deterministic provider stub that records method invocations."""

    def __init__(
        self,
        name: str,
        *,
        failures: dict[str, object] | None = None,
        embed_result: list[list[float]] | None = None,
        completion_result: str | None = None,
    ) -> None:
        from devsynth.adapters.provider_system import ProviderError

        self.name = name
        self.failures = failures or {}
        self.embed_result = embed_result or [[1.0]]
        self.completion_result = completion_result or f"{self.name}-complete"
        self.calls: list[tuple[str, dict]] = []
        self._provider_error = ProviderError

    def _record_call(self, method: str, **kwargs) -> None:
        self.calls.append((method, kwargs))

    def _maybe_fail(self, method: str) -> None:
        failure = self.failures.get(method)
        if failure is None:
            return
        if failure is True:
            raise self._provider_error(f"{self.name} {method} failure")
        if isinstance(failure, Exception):
            raise failure
        if isinstance(failure, type) and issubclass(failure, Exception):
            raise failure(f"{self.name} {method} failure")
        if callable(failure):
            raise failure()
        raise failure  # pragma: no cover - unexpected configuration

    def complete(
        self,
        *,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        parameters: dict | None = None,
    ) -> str:
        self._record_call(
            "complete",
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            parameters=parameters,
        )
        self._maybe_fail("complete")
        return self.completion_result

    async def acomplete(
        self,
        *,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        parameters: dict | None = None,
    ) -> str:
        self._record_call(
            "acomplete",
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            parameters=parameters,
        )
        self._maybe_fail("acomplete")
        return self.completion_result

    def embed(self, text) -> list[list[float]]:
        self._record_call("embed", text=text)
        self._maybe_fail("embed")
        return self.embed_result

    async def aembed(self, text) -> list[list[float]]:
        self._record_call("aembed", text=text)
        self._maybe_fail("aembed")
        return self.embed_result
