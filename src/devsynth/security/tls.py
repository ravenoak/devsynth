"""TLS configuration utilities."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import os


@dataclass
class TLSConfig:
    """Configuration for TLS connections."""

    verify: bool = True
    cert_file: Optional[str] = None
    key_file: Optional[str] = None
    ca_file: Optional[str] = None

    def validate(self) -> None:
        """Validate TLS certificate and key file paths."""
        for path, name in [
            (self.cert_file, "cert_file"),
            (self.key_file, "key_file"),
            (self.ca_file, "ca_file"),
        ]:
            if path and not os.path.exists(path):
                raise FileNotFoundError(f"{name} not found: {path}")

    def as_requests_kwargs(self) -> dict:
        """Return kwargs for requests/httpx methods."""
        kwargs = {"verify": self.ca_file or self.verify}
        if self.cert_file and self.key_file:
            kwargs["cert"] = (self.cert_file, self.key_file)
        elif self.cert_file:
            kwargs["cert"] = self.cert_file
        return kwargs
