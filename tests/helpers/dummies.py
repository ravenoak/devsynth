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
