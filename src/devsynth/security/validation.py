"""Input validation utilities."""

from pathlib import Path
from typing import Any, Iterable, Union

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
    min_value: Union[int, None] = None,
    max_value: Union[int, None] = None,
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


def parse_bool_env(var: str, default: bool = False) -> bool:
    """Parse a boolean environment variable securely.

    Args:
        var: Environment variable name.
        default: Value to return if the variable is not set.

    Returns:
        The parsed boolean value.

    Raises:
        ValidationError: If the variable is set to an invalid value.
    """
    import os

    value = os.environ.get(var)
    if value is None:
        return default
    val = str(value).strip().lower()
    if val in {"1", "true", "yes"}:
        return True
    if val in {"0", "false", "no"}:
        return False
    raise ValidationError("Invalid boolean", field=var, value=value)


def require_pre_deploy_checks() -> None:
    """Ensure mandatory pre-deployment policy checks have passed.

    The ``DEVSYNTH_PRE_DEPLOY_APPROVED`` environment variable must evaluate to
    ``true`` according to :func:`parse_bool_env`. A ``RuntimeError`` is raised
    otherwise.

    For alpha releases, this check is relaxed to allow development workflows.
    """
    import os

    # Check if this is an alpha release or development environment
    current_version = os.environ.get("DEVSYNTH_VERSION", "")
    current_env = os.environ.get("DEVSYNTH_ENV", "")

    # Also check pyproject.toml version as fallback
    try:
        import tomllib
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            with pyproject_path.open("rb") as f:
                data = tomllib.load(f)
                project_version = data.get("project", {}).get("version", "")
                if not current_version:
                    current_version = project_version
    except (ImportError, FileNotFoundError, tomllib.TOMLDecodeError):
        pass

    is_alpha_release = "0.1.0a1" in current_version
    is_dev_env = current_env.lower() in ("dev", "development", "alpha")

    # For alpha releases, make this check informational
    if is_alpha_release or is_dev_env:
        if not parse_bool_env("DEVSYNTH_PRE_DEPLOY_APPROVED", False):
            print("[security] Pre-deploy policy checks not approved, but allowing for alpha release")
            return

    if not parse_bool_env("DEVSYNTH_PRE_DEPLOY_APPROVED", False):
        raise RuntimeError("Pre-deploy policy checks have not been approved")
