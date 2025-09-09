"""Authentication utilities using Argon2 password hashing.

Security defaults:
- Use Argon2id (PasswordHasher default) with explicit safe parameters.
- Provide strong memory and time cost to resist GPU attacks.
These values follow widely recommended baselines and can be revised centrally.
"""

from typing import Dict

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from devsynth.exceptions import AuthenticationError

from .validation import parse_bool_env

# Argon2id safe defaults (see OWASP and PHC recommendations)
# Note: tune memory_cost based on deployment constraints.
_ARGON2_TIME_COST = 3
_ARGON2_MEMORY_COST = 65536  # in KiB (64 MiB)
_ARGON2_PARALLELISM = 4
_ARGON2_HASH_LEN = 32
_ARGON2_SALT_LEN = 16

# Argon2 password hasher instance (Argon2id by default)
_password_hasher = PasswordHasher(
    time_cost=_ARGON2_TIME_COST,
    memory_cost=_ARGON2_MEMORY_COST,
    parallelism=_ARGON2_PARALLELISM,
    hash_len=_ARGON2_HASH_LEN,
    salt_len=_ARGON2_SALT_LEN,
)


def hash_password(password: str) -> str:
    """Hash a plain text password using Argon2."""
    return _password_hasher.hash(password)


def verify_password(stored_hash: str, password: str) -> bool:
    """Verify a password against an existing Argon2 hash."""
    try:
        return _password_hasher.verify(stored_hash, password)
    except VerifyMismatchError:
        return False


def authenticate(username: str, password: str, credentials: Dict[str, str]) -> bool:
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

    if username not in credentials:
        raise AuthenticationError("Unknown username", details={"username": username})

    if not verify_password(credentials[username], password):
        raise AuthenticationError("Invalid credentials", details={"username": username})

    return True
