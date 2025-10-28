"""Simple role-based authorization utilities."""

from typing import Dict
from collections.abc import Iterable

from devsynth.exceptions import AuthorizationError

from .validation import parse_bool_env


def is_authorized(
    user_roles: Iterable[str], action: str, acl: dict[str, Iterable[str]]
) -> bool:
    """Check whether any of the user's roles grants access to the action.

    Args:
        user_roles: Roles associated with the user.
        action: Action being attempted.
        acl: Mapping of role names to allowed actions.

    Returns:
        True if authorized, False otherwise.
    """
    if not parse_bool_env("DEVSYNTH_AUTHORIZATION_ENABLED", True):
        return True

    for role in user_roles:
        allowed = acl.get(role, [])
        if action in allowed or "*" in allowed:
            return True
    return False


def require_authorization(
    user_roles: Iterable[str], action: str, acl: dict[str, Iterable[str]]
) -> None:
    """Raise AuthorizationError if the user is not permitted to perform the action."""
    if not is_authorized(user_roles, action, acl):
        raise AuthorizationError(
            "Permission denied",
            details={"roles": list(user_roles), "action": action},
        )
