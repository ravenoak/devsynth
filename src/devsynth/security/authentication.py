"""Authentication utilities using Argon2 password hashing."""

from typing import Dict
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from devsynth.exceptions import AuthenticationError

# Argon2 password hasher instance
_password_hasher = PasswordHasher()


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
    if username not in credentials:
        raise AuthenticationError("Unknown username", details={"username": username})

    if not verify_password(credentials[username], password):
        raise AuthenticationError("Invalid credentials", details={"username": username})

    return True
