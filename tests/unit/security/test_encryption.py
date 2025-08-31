import os

import pytest
from cryptography.fernet import Fernet, InvalidToken

from devsynth.security.encryption import (
    _DEFAULT_ENV_KEY,
    _get_fernet,
    decrypt_bytes,
    encrypt_bytes,
    generate_key,
)


@pytest.mark.fast
def test_generate_key_returns_expected_result():
    """Test that generate_key returns a valid Fernet key.

    ReqID: N/A"""
    key = generate_key()
    assert isinstance(key, str)
    fernet = Fernet(key.encode())
    assert isinstance(fernet, Fernet)


@pytest.mark.fast
def test_encrypt_decrypt_roundtrip_succeeds():
    """Test that data can be encrypted and then decrypted back to the original data.

    ReqID: N/A"""
    key = generate_key()
    data = b"secret"
    token = encrypt_bytes(data, key)
    assert data != token
    plain = decrypt_bytes(token, key)
    assert plain == data


@pytest.mark.fast
def test_get_fernet_with_key_succeeds():
    """Test that _get_fernet works with a key provided as a parameter.

    ReqID: N/A"""
    key = generate_key()
    fernet = _get_fernet(key)
    assert isinstance(fernet, Fernet)


@pytest.mark.fast
def test_get_fernet_with_string_key_succeeds():
    """Test that _get_fernet works with a key provided as a string.

    ReqID: N/A"""
    key = generate_key()
    fernet = _get_fernet(key)
    assert isinstance(fernet, Fernet)
    data = b"test data"
    token = fernet.encrypt(data)
    decrypted = fernet.decrypt(token)
    assert decrypted == data


@pytest.mark.fast
def test_get_fernet_with_bytes_key_succeeds():
    """Test that _get_fernet works with a key provided as bytes.

    ReqID: N/A"""
    key = generate_key().encode()
    fernet = _get_fernet(key)
    assert isinstance(fernet, Fernet)
    data = b"test data"
    token = fernet.encrypt(data)
    decrypted = fernet.decrypt(token)
    assert decrypted == data


@pytest.mark.fast
def test_get_fernet_with_env_var_succeeds(monkeypatch):
    """Test that _get_fernet works with a key from the environment variable.

    ReqID: N/A"""
    key = generate_key()
    monkeypatch.setenv(_DEFAULT_ENV_KEY, key)
    fernet = _get_fernet()
    assert isinstance(fernet, Fernet)


@pytest.mark.fast
def test_get_fernet_no_key_raises_error(monkeypatch):
    """Test that _get_fernet raises ValueError when no key is provided.

    ReqID: N/A"""
    monkeypatch.delenv(_DEFAULT_ENV_KEY, raising=False)
    with pytest.raises(ValueError) as excinfo:
        _get_fernet()
    assert "Encryption key not provided" in str(excinfo.value)


@pytest.mark.fast
def test_encrypt_decrypt_with_env_var_succeeds(monkeypatch):
    """Test that encrypt_bytes and decrypt_bytes work with a key from the environment variable.

    ReqID: N/A"""
    key = generate_key()
    monkeypatch.setenv(_DEFAULT_ENV_KEY, key)
    data = b"secret"
    token = encrypt_bytes(data)
    assert data != token
    plain = decrypt_bytes(token)
    assert plain == data


@pytest.mark.fast
def test_decrypt_invalid_token_raises_error():
    """Test that decrypt_bytes raises InvalidToken when given an invalid token.

    ReqID: N/A"""
    key = generate_key()
    invalid_token = b"invalid token"
    with pytest.raises(InvalidToken):
        decrypt_bytes(invalid_token, key)


@pytest.mark.fast
def test_decrypt_with_wrong_key_raises_error():
    """Test that decrypt_bytes raises InvalidToken when given a valid token but the wrong key.

    ReqID: N/A"""
    key1 = generate_key()
    key2 = generate_key()
    assert key1 != key2
    data = b"secret"
    token = encrypt_bytes(data, key1)
    with pytest.raises(InvalidToken):
        decrypt_bytes(token, key2)
