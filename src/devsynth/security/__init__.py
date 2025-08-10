"""Security utilities for DevSynth."""

from .audit import audit_event
from .authentication import authenticate, hash_password, verify_password
from .authorization import is_authorized
from .deployment import (
    apply_secure_umask,
    check_required_env_vars,
    harden_runtime,
    require_non_root_user,
)
from .encryption import decrypt_bytes, encrypt_bytes, generate_key
from .review import is_review_due, next_review_date
from .sanitization import sanitize_input, validate_safe_input
from .tls import TLSConfig
from .validation import (
    parse_bool_env,
    validate_choice,
    validate_int_range,
    validate_non_empty,
)

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
    "is_review_due",
    "next_review_date",
    "harden_runtime",
    "require_non_root_user",
    "check_required_env_vars",
    "apply_secure_umask",
]
