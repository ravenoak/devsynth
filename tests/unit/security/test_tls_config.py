import os
import pytest
from devsynth.security.tls import TLSConfig


def test_tls_config_validation_raises_error(tmp_path):
    """Test that validate doesn't raise an exception when the certificate and key files exist.

ReqID: N/A"""
    cert = tmp_path / 'cert.pem'
    key = tmp_path / 'key.pem'
    ca = tmp_path / 'ca.pem'
    cert.write_text('cert')
    key.write_text('key')
    ca.write_text('ca')
    cfg = TLSConfig(cert_file=str(cert), key_file=str(key), ca_file=str(ca))
    cfg.validate()


def test_tls_config_validation_partial_raises_error(tmp_path):
    """Test that validate raises an exception when some files exist and some don't.

ReqID: N/A"""
    cert = tmp_path / 'cert.pem'
    key = tmp_path / 'key.pem'
    missing_ca = tmp_path / 'missing_ca.pem'
    cert.write_text('cert')
    key.write_text('key')
    cfg = TLSConfig(cert_file=str(cert), key_file=str(key), ca_file=str(
        missing_ca))
    with pytest.raises(FileNotFoundError) as excinfo:
        cfg.validate()
    assert 'ca_file not found' in str(excinfo.value)


def test_tls_config_validation_key_only_succeeds(tmp_path):
    """Test that validate works with only a key file.

ReqID: N/A"""
    key = tmp_path / 'key.pem'
    key.write_text('key')
    cfg = TLSConfig(key_file=str(key))
    cfg.validate()


def test_tls_config_validation_cert_only_succeeds(tmp_path):
    """Test that validate works with only a cert file.

ReqID: N/A"""
    cert = tmp_path / 'cert.pem'
    cert.write_text('cert')
    cfg = TLSConfig(cert_file=str(cert))
    cfg.validate()


def test_tls_config_validation_missing_raises_error(tmp_path):
    """Test that validate raises a FileNotFoundError when a file doesn't exist.

ReqID: N/A"""
    cfg = TLSConfig(cert_file=str(tmp_path / 'missing.pem'))
    with pytest.raises(FileNotFoundError) as excinfo:
        cfg.validate()
    assert 'cert_file not found' in str(excinfo.value)


def test_tls_config_as_requests_kwargs_default_succeeds():
    """Test as_requests_kwargs with default settings.

ReqID: N/A"""
    cfg = TLSConfig()
    kwargs = cfg.as_requests_kwargs()
    assert kwargs == {'verify': True}


def test_tls_config_as_requests_kwargs_verify_false_succeeds():
    """Test as_requests_kwargs with verify=False.

ReqID: N/A"""
    cfg = TLSConfig(verify=False)
    kwargs = cfg.as_requests_kwargs()
    assert kwargs == {'verify': False}


def test_tls_config_as_requests_kwargs_with_ca_file_has_expected(tmp_path):
    """Test as_requests_kwargs with ca_file provided.

ReqID: N/A"""
    ca = tmp_path / 'ca.pem'
    ca.write_text('ca')
    cfg = TLSConfig(ca_file=str(ca))
    kwargs = cfg.as_requests_kwargs()
    assert kwargs == {'verify': str(ca)}


def test_tls_config_as_requests_kwargs_with_cert_and_key_has_expected(tmp_path
    ):
    """Test as_requests_kwargs with cert_file and key_file provided.

ReqID: N/A"""
    cert = tmp_path / 'cert.pem'
    key = tmp_path / 'key.pem'
    cert.write_text('cert')
    key.write_text('key')
    cfg = TLSConfig(cert_file=str(cert), key_file=str(key))
    kwargs = cfg.as_requests_kwargs()
    assert kwargs == {'verify': True, 'cert': (str(cert), str(key))}


def test_tls_config_as_requests_kwargs_with_cert_only_has_expected(tmp_path):
    """Test as_requests_kwargs with only cert_file provided.

ReqID: N/A"""
    cert = tmp_path / 'cert.pem'
    cert.write_text('cert')
    cfg = TLSConfig(cert_file=str(cert))
    kwargs = cfg.as_requests_kwargs()
    assert kwargs == {'verify': True, 'cert': str(cert)}


def test_tls_config_as_requests_kwargs_ca_file_precedence_succeeds(tmp_path):
    """Test as_requests_kwargs with both ca_file and verify=False.

ReqID: N/A"""
    ca = tmp_path / 'ca.pem'
    ca.write_text('ca')
    cfg = TLSConfig(ca_file=str(ca), verify=False)
    kwargs = cfg.as_requests_kwargs()
    assert kwargs == {'verify': str(ca)}


def test_tls_config_as_requests_kwargs_all_params_succeeds(tmp_path):
    """Test as_requests_kwargs with all parameters set.

ReqID: N/A"""
    cert = tmp_path / 'cert.pem'
    key = tmp_path / 'key.pem'
    ca = tmp_path / 'ca.pem'
    cert.write_text('cert')
    key.write_text('key')
    ca.write_text('ca')
    cfg = TLSConfig(verify=True, cert_file=str(cert), key_file=str(key),
        ca_file=str(ca))
    kwargs = cfg.as_requests_kwargs()
    assert kwargs == {'verify': str(ca), 'cert': (str(cert), str(key))}
