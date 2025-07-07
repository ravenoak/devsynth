import os
import pytest
from devsynth.security.tls import TLSConfig


def test_tls_config_validation(tmp_path):
    """Test that validate doesn't raise an exception when the certificate and key files exist."""
    cert = tmp_path / "cert.pem"
    key = tmp_path / "key.pem"
    ca = tmp_path / "ca.pem"
    cert.write_text("cert")
    key.write_text("key")
    ca.write_text("ca")
    cfg = TLSConfig(cert_file=str(cert), key_file=str(key), ca_file=str(ca))
    cfg.validate()  # should not raise


def test_tls_config_validation_partial(tmp_path):
    """Test that validate raises an exception when some files exist and some don't."""
    cert = tmp_path / "cert.pem"
    key = tmp_path / "key.pem"
    missing_ca = tmp_path / "missing_ca.pem"
    cert.write_text("cert")
    key.write_text("key")

    # Create config with existing cert and key but missing ca
    cfg = TLSConfig(cert_file=str(cert), key_file=str(key), ca_file=str(missing_ca))
    with pytest.raises(FileNotFoundError) as excinfo:
        cfg.validate()
    assert "ca_file not found" in str(excinfo.value)


def test_tls_config_validation_key_only(tmp_path):
    """Test that validate works with only a key file."""
    key = tmp_path / "key.pem"
    key.write_text("key")

    cfg = TLSConfig(key_file=str(key))
    cfg.validate()  # should not raise


def test_tls_config_validation_cert_only(tmp_path):
    """Test that validate works with only a cert file."""
    cert = tmp_path / "cert.pem"
    cert.write_text("cert")

    cfg = TLSConfig(cert_file=str(cert))
    cfg.validate()  # should not raise


def test_tls_config_validation_missing(tmp_path):
    """Test that validate raises a FileNotFoundError when a file doesn't exist."""
    cfg = TLSConfig(cert_file=str(tmp_path / "missing.pem"))
    with pytest.raises(FileNotFoundError) as excinfo:
        cfg.validate()
    assert "cert_file not found" in str(excinfo.value)


def test_tls_config_as_requests_kwargs_default():
    """Test as_requests_kwargs with default settings."""
    cfg = TLSConfig()
    kwargs = cfg.as_requests_kwargs()
    assert kwargs == {"verify": True}


def test_tls_config_as_requests_kwargs_verify_false():
    """Test as_requests_kwargs with verify=False."""
    cfg = TLSConfig(verify=False)
    kwargs = cfg.as_requests_kwargs()
    assert kwargs == {"verify": False}


def test_tls_config_as_requests_kwargs_with_ca_file(tmp_path):
    """Test as_requests_kwargs with ca_file provided."""
    ca = tmp_path / "ca.pem"
    ca.write_text("ca")
    cfg = TLSConfig(ca_file=str(ca))
    kwargs = cfg.as_requests_kwargs()
    assert kwargs == {"verify": str(ca)}


def test_tls_config_as_requests_kwargs_with_cert_and_key(tmp_path):
    """Test as_requests_kwargs with cert_file and key_file provided."""
    cert = tmp_path / "cert.pem"
    key = tmp_path / "key.pem"
    cert.write_text("cert")
    key.write_text("key")
    cfg = TLSConfig(cert_file=str(cert), key_file=str(key))
    kwargs = cfg.as_requests_kwargs()
    assert kwargs == {"verify": True, "cert": (str(cert), str(key))}


def test_tls_config_as_requests_kwargs_with_cert_only(tmp_path):
    """Test as_requests_kwargs with only cert_file provided."""
    cert = tmp_path / "cert.pem"
    cert.write_text("cert")
    cfg = TLSConfig(cert_file=str(cert))
    kwargs = cfg.as_requests_kwargs()
    assert kwargs == {"verify": True, "cert": str(cert)}


def test_tls_config_as_requests_kwargs_ca_file_precedence(tmp_path):
    """Test as_requests_kwargs with both ca_file and verify=False."""
    ca = tmp_path / "ca.pem"
    ca.write_text("ca")

    # When both ca_file and verify=False are provided, ca_file should take precedence
    cfg = TLSConfig(ca_file=str(ca), verify=False)
    kwargs = cfg.as_requests_kwargs()
    assert kwargs == {"verify": str(ca)}


def test_tls_config_as_requests_kwargs_all_params(tmp_path):
    """Test as_requests_kwargs with all parameters set."""
    cert = tmp_path / "cert.pem"
    key = tmp_path / "key.pem"
    ca = tmp_path / "ca.pem"
    cert.write_text("cert")
    key.write_text("key")
    ca.write_text("ca")

    # Create config with all parameters
    cfg = TLSConfig(
        verify=True,
        cert_file=str(cert),
        key_file=str(key),
        ca_file=str(ca)
    )

    kwargs = cfg.as_requests_kwargs()
    assert kwargs == {
        "verify": str(ca),
        "cert": (str(cert), str(key))
    }
