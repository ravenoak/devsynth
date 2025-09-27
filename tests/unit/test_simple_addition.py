import pytest

from devsynth.simple_addition import add


@pytest.mark.fast
def test_add_returns_sum_for_integers():
    assert add(2, 3) == 5


@pytest.mark.fast
def test_add_accepts_floats_and_mixed_numeric_types():
    assert add(2.5, 1.5) == 4.0
    # mixed int and float
    assert add(2, 0.5) == 2.5


@pytest.mark.fast
def test_add_raises_type_error_for_non_numeric_inputs():
    with pytest.raises(TypeError):
        add("2", 3)
    with pytest.raises(TypeError):
        add(2, object())
