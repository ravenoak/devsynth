import pytest

from devsynth.exceptions import (
    DevSynthError,
    InternalError,
    ValidationError,
    ensure_dev_synth_error,
)


@pytest.mark.fast
def test_dev_synth_error_to_dict():
    """DevSynthError exposes structured dictionary.

    ReqID: FR-97"""

    err = DevSynthError("boom", error_code="E1", details={"a": 1})
    assert err.to_dict() == {
        "error_type": "DevSynthError",
        "error_code": "E1",
        "message": "boom",
        "details": {"a": 1},
    }


@pytest.mark.fast
def test_ensure_dev_synth_error_wraps_and_passes_through():
    """Utility converts external errors to DevSynthError.

    ReqID: FR-97"""

    original = ValidationError("bad", field="name")
    wrapped = ensure_dev_synth_error(ValueError("bad"))
    assert isinstance(wrapped, InternalError)
    assert isinstance(ensure_dev_synth_error(original), ValidationError)
