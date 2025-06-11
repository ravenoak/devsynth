"""Input validation utilities."""

from typing import Any, Iterable

from devsynth.exceptions import ValidationError


def validate_non_empty(value: str, field: str) -> str:
    """Ensure the given string is not empty."""
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("Value cannot be empty", field=field, value=value)
    return value


def validate_int_range(
    value: Any,
    field: str,
    *,
    min_value: int | None = None,
    max_value: int | None = None
) -> int:
    """Validate that a value is an int within an optional range."""
    try:
        ivalue = int(value)
    except (TypeError, ValueError):
        raise ValidationError("Invalid integer", field=field, value=value)

    if min_value is not None and ivalue < min_value:
        raise ValidationError(
            "Value below minimum",
            field=field,
            value=ivalue,
            constraints={"min": min_value},
        )
    if max_value is not None and ivalue > max_value:
        raise ValidationError(
            "Value above maximum",
            field=field,
            value=ivalue,
            constraints={"max": max_value},
        )
    return ivalue


def validate_choice(value: Any, field: str, choices: Iterable[Any]) -> Any:
    """Ensure a value is one of the allowed choices."""
    if value not in choices:
        raise ValidationError(
            "Invalid choice",
            field=field,
            value=value,
            constraints={"choices": list(choices)},
        )
    return value
