"""Authentication utilities using Argon2 password hashing.

Security defaults:
- Use Argon2id (PasswordHasher default) with explicit safe parameters.
- Provide strong memory and time cost to resist GPU attacks.
These values follow widely recommended baselines and can be revised centrally.
"""

from typing import Dict, Optional, Protocol, cast

from devsynth.exceptions import AuthenticationError

from .validation import parse_bool_env

# Argon2id safe defaults (see OWASP and PHC recommendations)
# Note: tune memory_cost based on deployment constraints.
_ARGON2_TIME_COST = 3
_ARGON2_MEMORY_COST = 65536  # in KiB (64 MiB)
_ARGON2_PARALLELISM = 4
_ARGON2_HASH_LEN = 32
_ARGON2_SALT_LEN = 16


class _PasswordHasherProtocol(Protocol):
    """Protocol capturing the subset of the Argon2 password hasher we rely on."""

    def hash(self, password: str) -> str:
        """Hash a password and return the encoded representation."""

    def verify(self, stored_hash: str, password: str) -> bool:
        """Verify a password against a stored hash."""


_password_hasher: _PasswordHasherProtocol | None
_argon2_import_error: ImportError | None

try:
    from argon2 import PasswordHasher as _Argon2PasswordHasher
    from argon2.exceptions import VerifyMismatchError

    _password_hasher = _Argon2PasswordHasher(
        time_cost=_ARGON2_TIME_COST,
        memory_cost=_ARGON2_MEMORY_COST,
        parallelism=_ARGON2_PARALLELISM,
        hash_len=_ARGON2_HASH_LEN,
        salt_len=_ARGON2_SALT_LEN,
    )
    _argon2_import_error = None
except ImportError as argon2_exc:  # pragma: no cover - exercised via stub

    class VerifyMismatchError(Exception):
        """Fallback stub raised when Argon2 is unavailable."""

    _password_hasher = None
    _argon2_import_error = ImportError(
        "Argon2 support is required when authentication is enabled. "
        "Install the 'security' extra (for example, 'poetry install --with dev "
        '--extras "security"\') or install DevSynth with '
        "'pip install devsynth[security]'."
    )
    _argon2_import_error.__cause__ = argon2_exc


def _require_password_hasher() -> _PasswordHasherProtocol:
    """Return the configured password hasher or raise a guided ImportError."""

    if _password_hasher is None:
        assert _argon2_import_error is not None
        raise _argon2_import_error
    return _password_hasher


def hash_password(password: str) -> str:
    """Hash a plain text password using Argon2."""

    hasher = _require_password_hasher()
    return cast(str, hasher.hash(password))


def verify_password(stored_hash: str, password: str) -> bool:
    """Verify a password against an existing Argon2 hash."""

    try:
        hasher = _require_password_hasher()
        return bool(hasher.verify(stored_hash, password))
    except VerifyMismatchError:
        return False


def authenticate(username: str, password: str, credentials: dict[str, str]) -> bool:
    """Authenticate a user using a dictionary of stored Argon2 hashes.

    Args:
        username: Username to authenticate.
        password: Plain text password supplied by the user.
        credentials: Mapping of usernames to stored password hashes.

    Returns:
        True if authentication succeeds.

    Raises:
        AuthenticationError: If the username is unknown or the password is invalid.
    """

    # Allow bypassing authentication if explicitly disabled via env var
    if not parse_bool_env("DEVSYNTH_AUTHENTICATION_ENABLED", True):
        return True

    if _password_hasher is None:
        assert _argon2_import_error is not None
        raise _argon2_import_error

    if username not in credentials:
        raise AuthenticationError("Unknown username", details={"username": username})

    if not verify_password(credentials[username], password):
        raise AuthenticationError("Invalid credentials", details={"username": username})

    return True
