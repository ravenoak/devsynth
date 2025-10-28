"""TLS configuration utilities.

This module provides a small, dependency-light configuration object that
normalizes TLS and HTTP client keyword arguments across both `requests`
and `httpx` without introducing hard dependencies on either library.

Security posture: we also centralize the default HTTP timeout here to
ensure every network call in adapters consistently uses explicit timeouts.
The timeout can be overridden via the environment variable
`DEVSYNTH_HTTP_TIMEOUT` (seconds).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class TLSConfig:
    """Configuration for TLS connections and HTTP client behavior.

    Attributes:
        verify: Whether to verify TLS certificates. If `ca_file` is set,
            that path will be used as the verification source.
        cert_file: Optional path to a client certificate file.
        key_file: Optional path to the corresponding private key file.
        ca_file: Optional path to a CA bundle or certificate.
        timeout: Default network timeout in seconds applied to both
            `requests` and `httpx` calls that accept a `timeout` kwarg.
            When None, a sane default from `DEVSYNTH_HTTP_TIMEOUT` is used.
    """

    verify: bool = True
    cert_file: str | None = None
    key_file: str | None = None
    ca_file: str | None = None
    timeout: float | None = None

    def validate(self) -> None:
        """Validate TLS certificate and key file paths."""
        for path, name in [
            (self.cert_file, "cert_file"),
            (self.key_file, "key_file"),
            (self.ca_file, "ca_file"),
        ]:
            if path and not os.path.exists(path):
                raise FileNotFoundError(f"{name} not found: {path}")

    def as_requests_kwargs(self) -> dict[str, bool | str | tuple[str, str] | float]:
        """Return kwargs for requests/httpx methods.

        Includes:
        - verify/cert settings derived from TLS config
        - timeout (float seconds) sourced from `self.timeout` or
          `DEVSYNTH_HTTP_TIMEOUT` env var (default: 10.0 seconds)
        """
        kwargs: dict[str, bool | str | tuple[str, str] | float] = {
            "verify": self.verify
        }
        if self.ca_file:
            kwargs["verify"] = self.ca_file
        if self.cert_file and self.key_file:
            kwargs["cert"] = (self.cert_file, self.key_file)
        elif self.cert_file:
            kwargs["cert"] = self.cert_file

        # Provide an explicit timeout for all HTTP calls using this config
        if self.timeout is not None:
            timeout_val: float = float(self.timeout)
        else:
            # Default to 10 seconds if not explicitly configured
            timeout_val = float(os.environ.get("DEVSYNTH_HTTP_TIMEOUT", "10"))
        kwargs["timeout"] = timeout_val

        return kwargs
