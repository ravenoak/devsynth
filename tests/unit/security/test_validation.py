from devsynth.security.validation import (
    validate_non_empty,
    validate_int_range,
    validate_choice,
)
from devsynth.exceptions import ValidationError


def test_validate_non_empty_success():
    assert validate_non_empty("x", "field") == "x"


def test_validate_non_empty_fail():
    try:
        validate_non_empty("", "field")
    except ValidationError:
        assert True
    else:
        assert False


def test_validate_int_range():
    assert validate_int_range("5", "num", min_value=1, max_value=10) == 5
    try:
        validate_int_range("0", "num", min_value=1)
    except ValidationError:
        assert True
    else:
        assert False


def test_validate_choice():
    assert validate_choice("a", "f", ["a", "b"]) == "a"
    try:
        validate_choice("c", "f", ["a", "b"])
    except ValidationError:
        assert True
    else:
        assert False
