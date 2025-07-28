"""Security utilities for DevSynth."""

from .authentication import hash_password, verify_password, authenticate
from .authorization import is_authorized
from .sanitization import sanitize_input, validate_safe_input
from .encryption import generate_key, encrypt_bytes, decrypt_bytes
from .validation import (
    validate_non_empty,
    validate_int_range,
    validate_choice,
    parse_bool_env,
)
from .tls import TLSConfig
from .audit import audit_event

__all__ = [
    "hash_password",
    "verify_password",
    "authenticate",
    "is_authorized",
    "sanitize_input",
    "validate_safe_input",
    "generate_key",
    "encrypt_bytes",
    "decrypt_bytes",
    "audit_event",
    "validate_non_empty",
    "validate_int_range",
    "validate_choice",
    "parse_bool_env",
    "TLSConfig",
]
