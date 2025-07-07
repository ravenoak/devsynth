import pytest
from devsynth.security.validation import (
    validate_non_empty,
    validate_int_range,
    validate_choice,
)
from devsynth.exceptions import ValidationError


class TestValidateNonEmpty:
    """Tests for validate_non_empty function."""

    def test_valid_string(self):
        """Test with valid non-empty string."""
        assert validate_non_empty("x", "field") == "x"
        assert validate_non_empty("hello", "field") == "hello"
        assert validate_non_empty("  hello  ", "field") == "  hello  "

    @pytest.mark.parametrize("invalid_value", ["", "   ", None])
    def test_invalid_string(self, invalid_value):
        """Test with invalid empty strings or None."""
        with pytest.raises(ValidationError) as excinfo:
            validate_non_empty(invalid_value, "test_field")

        assert excinfo.value.details["field"] == "test_field"
        assert excinfo.value.details["value"] == invalid_value

    def test_non_string_value(self):
        """Test with non-string values."""
        with pytest.raises(ValidationError):
            validate_non_empty(123, "number_field")

        with pytest.raises(ValidationError):
            validate_non_empty(True, "bool_field")

        with pytest.raises(ValidationError):
            validate_non_empty([], "list_field")


class TestValidateIntRange:
    """Tests for validate_int_range function."""

    @pytest.mark.parametrize("value,expected", [
        ("5", 5),
        (5, 5),
        ("10", 10),
        ("-5", -5),
        ("0", 0)
    ])
    def test_valid_int(self, value, expected):
        """Test with valid integer values."""
        assert validate_int_range(value, "num") == expected

    @pytest.mark.parametrize("value,min_val,max_val,expected", [
        ("5", 1, 10, 5),
        ("1", 1, 10, 1),
        ("10", 1, 10, 10),
        ("-5", -10, 0, -5),
        ("0", -10, 10, 0)
    ])
    def test_valid_int_with_range(self, value, min_val, max_val, expected):
        """Test with valid integer values within range."""
        assert validate_int_range(value, "num", min_value=min_val, max_value=max_val) == expected

    @pytest.mark.parametrize("value", ["abc", "1.5", "", None, {}, []])
    def test_invalid_int(self, value):
        """Test with invalid integer values."""
        with pytest.raises(ValidationError) as excinfo:
            validate_int_range(value, "num_field")

        assert excinfo.value.details["field"] == "num_field"
        assert excinfo.value.details["value"] == value

    @pytest.mark.parametrize("value,min_val", [
        ("0", 1),
        ("-5", 0),
        ("5", 10)
    ])
    def test_below_min_value(self, value, min_val):
        """Test with values below minimum."""
        with pytest.raises(ValidationError) as excinfo:
            validate_int_range(value, "num_field", min_value=min_val)

        assert excinfo.value.details["field"] == "num_field"
        assert "below minimum" in excinfo.value.message.lower()
        assert excinfo.value.details["constraints"]["min"] == min_val

    @pytest.mark.parametrize("value,max_val", [
        ("10", 5),
        ("0", -1),
        ("100", 99)
    ])
    def test_above_max_value(self, value, max_val):
        """Test with values above maximum."""
        with pytest.raises(ValidationError) as excinfo:
            validate_int_range(value, "num_field", max_value=max_val)

        assert excinfo.value.details["field"] == "num_field"
        assert "above maximum" in excinfo.value.message.lower()
        assert excinfo.value.details["constraints"]["max"] == max_val


class TestValidateChoice:
    """Tests for validate_choice function."""

    @pytest.mark.parametrize("value,choices", [
        ("a", ["a", "b", "c"]),
        (1, [1, 2, 3]),
        (True, [True, False]),
        (None, [None, "value"]),
        ("value", {"value", "other"}),  # Test with set
        (5, (5, 10, 15))  # Test with tuple
    ])
    def test_valid_choice(self, value, choices):
        """Test with valid choices."""
        assert validate_choice(value, "choice_field", choices) == value

    @pytest.mark.parametrize("value,choices", [
        ("d", ["a", "b", "c"]),
        (4, [1, 2, 3]),
        (None, [True, False]),
        ("missing", {"value", "other"}),
        (20, (5, 10, 15))
    ])
    def test_invalid_choice(self, value, choices):
        """Test with invalid choices."""
        with pytest.raises(ValidationError) as excinfo:
            validate_choice(value, "choice_field", choices)

        assert excinfo.value.details["field"] == "choice_field"
        assert excinfo.value.details["value"] == value
        assert "invalid choice" in excinfo.value.message.lower()
        assert "choices" in excinfo.value.details["constraints"]
        assert set(excinfo.value.details["constraints"]["choices"]) == set(choices)
