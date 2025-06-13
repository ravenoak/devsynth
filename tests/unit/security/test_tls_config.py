import os
import pytest
from devsynth.security.tls import TLSConfig


def test_tls_config_validation(tmp_path):
    cert = tmp_path / "cert.pem"
    key = tmp_path / "key.pem"
    ca = tmp_path / "ca.pem"
    cert.write_text("cert")
    key.write_text("key")
    ca.write_text("ca")
    cfg = TLSConfig(cert_file=str(cert), key_file=str(key), ca_file=str(ca))
    cfg.validate()  # should not raise


def test_tls_config_validation_missing(tmp_path):
    cfg = TLSConfig(cert_file=str(tmp_path / "missing.pem"))
    with pytest.raises(FileNotFoundError):
        cfg.validate()
