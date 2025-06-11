"""TLS configuration utilities."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class TLSConfig:
    """Configuration for TLS connections."""

    verify: bool = True
    cert_file: Optional[str] = None
    key_file: Optional[str] = None
    ca_file: Optional[str] = None

    def as_requests_kwargs(self) -> dict:
        """Return kwargs for requests/httpx methods."""
        kwargs = {"verify": self.ca_file or self.verify}
        if self.cert_file and self.key_file:
            kwargs["cert"] = (self.cert_file, self.key_file)
        elif self.cert_file:
            kwargs["cert"] = self.cert_file
        return kwargs
