from typing import Any

import pytest

from devsynth.application.promises.interface import PromiseInterface

pytestmark = [pytest.mark.fast]


class DummyPromise(PromiseInterface[int]):
    @property
    def id(self) -> str:  # pragma: no cover - intentional
        return super().id

    @property
    def state(self):  # pragma: no cover - intentional
        return super().state

    @property
    def is_pending(self) -> bool:  # pragma: no cover - intentional
        return super().is_pending

    @property
    def is_fulfilled(self) -> bool:  # pragma: no cover - intentional
        return super().is_fulfilled

    @property
    def is_rejected(self) -> bool:  # pragma: no cover - intentional
        return super().is_rejected

    @property
    def value(self) -> int:  # pragma: no cover - intentional
        return super().value

    @property
    def reason(self) -> Exception:  # pragma: no cover - intentional
        return super().reason

    def set_metadata(self, key: str, value: Any):  # pragma: no cover - intentional
        return super().set_metadata(key, value)

    def get_metadata(self, key: str):  # pragma: no cover - intentional
        return super().get_metadata(key)

    def then(self, on_fulfilled, on_rejected=None):  # pragma: no cover - intentional
        return super().then(on_fulfilled, on_rejected)

    def catch(self, on_rejected):  # pragma: no cover - intentional
        return super().catch(on_rejected)

    def resolve(self, value: int) -> None:  # pragma: no cover - intentional
        super().resolve(value)

    def reject(self, reason: Exception) -> None:  # pragma: no cover - intentional
        super().reject(reason)


def test_promise_interface_id_not_implemented() -> None:
    promise = DummyPromise()
    with pytest.raises(NotImplementedError):
        _ = promise.id
