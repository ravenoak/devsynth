from __future__ import annotations

"""Simple encryption helpers using Fernet symmetric encryption.

Security defaults:
- Keys must be valid 32-byte urlsafe base64 (44-char string) generated via Fernet.generate_key().
- Key is read from DEVSYNTH_ENCRYPTION_KEY unless explicitly provided.
"""

import base64
import os
from typing import Optional

from cryptography.fernet import Fernet

_DEFAULT_ENV_KEY = "DEVSYNTH_ENCRYPTION_KEY"


def generate_key() -> str:
    """Generate a base64 encoded Fernet key."""
    return Fernet.generate_key().decode()


def _validate_key_format(key_bytes: bytes) -> None:
    """Validate the Fernet key format and length.

    Raises ValueError with an actionable message if invalid.
    """
    try:
        raw = base64.urlsafe_b64decode(key_bytes)
    except Exception as e:  # pragma: no cover - defensive
        raise ValueError("Encryption key must be urlsafe base64-encoded") from e
    if len(raw) != 32:
        raise ValueError("Encryption key must decode to 32 bytes (Fernet format)")


def _get_fernet(key: Optional[str] = None) -> Fernet:
    key_bytes = key or os.environ.get(_DEFAULT_ENV_KEY)
    if not key_bytes:
        raise ValueError("Encryption key not provided")
    if isinstance(key_bytes, str):
        key_bytes = key_bytes.encode()
    _validate_key_format(key_bytes)
    return Fernet(key_bytes)


def encrypt_bytes(data: bytes, key: Optional[str] = None) -> bytes:
    """Encrypt bytes using Fernet."""
    return _get_fernet(key).encrypt(data)


def decrypt_bytes(token: bytes, key: Optional[str] = None) -> bytes:
    """Decrypt bytes using Fernet."""
    return _get_fernet(key).decrypt(token)
