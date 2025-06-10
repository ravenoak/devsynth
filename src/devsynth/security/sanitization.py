"""Input sanitization helpers for DevSynth."""

import re
from devsynth.exceptions import InputSanitizationError

_SCRIPT_TAG_RE = re.compile(r"<script.*?>.*?</script>", re.IGNORECASE | re.DOTALL)
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f]")


def sanitize_input(text: str) -> str:
    """Remove dangerous content from a text string."""
    text = _SCRIPT_TAG_RE.sub("", text)
    text = _CONTROL_CHAR_RE.sub("", text)
    return text.strip()


def validate_safe_input(text: str) -> str:
    """Sanitize and validate that text is safe.

    Raises InputSanitizationError if content is modified.
    """
    sanitized = sanitize_input(text)
    if sanitized != text:
        raise InputSanitizationError("Unsafe input detected", details={"input": text})
    return sanitized
