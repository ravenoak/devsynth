import os
import pytest
from cryptography.fernet import Fernet, InvalidToken
from devsynth.security.encryption import (
    generate_key, encrypt_bytes, decrypt_bytes, _get_fernet, _DEFAULT_ENV_KEY
)


def test_generate_key():
    """Test that generate_key returns a valid Fernet key."""
    key = generate_key()
    assert isinstance(key, str)
    # Verify that the key is a valid Fernet key by creating a Fernet instance
    fernet = Fernet(key.encode())
    assert isinstance(fernet, Fernet)


def test_encrypt_decrypt_roundtrip():
    """Test that data can be encrypted and then decrypted back to the original data."""
    key = generate_key()
    data = b"secret"
    token = encrypt_bytes(data, key)
    assert data != token
    plain = decrypt_bytes(token, key)
    assert plain == data


def test_get_fernet_with_key():
    """Test that _get_fernet works with a key provided as a parameter."""
    key = generate_key()
    fernet = _get_fernet(key)
    assert isinstance(fernet, Fernet)


def test_get_fernet_with_string_key():
    """Test that _get_fernet works with a key provided as a string."""
    key = generate_key()
    # Key is already a string, no need to encode
    fernet = _get_fernet(key)
    assert isinstance(fernet, Fernet)

    # Verify that the fernet instance works
    data = b"test data"
    token = fernet.encrypt(data)
    decrypted = fernet.decrypt(token)
    assert decrypted == data


def test_get_fernet_with_bytes_key():
    """Test that _get_fernet works with a key provided as bytes."""
    key = generate_key().encode()  # Convert to bytes
    fernet = _get_fernet(key)
    assert isinstance(fernet, Fernet)

    # Verify that the fernet instance works
    data = b"test data"
    token = fernet.encrypt(data)
    decrypted = fernet.decrypt(token)
    assert decrypted == data


def test_get_fernet_with_env_var(monkeypatch):
    """Test that _get_fernet works with a key from the environment variable."""
    key = generate_key()
    monkeypatch.setenv(_DEFAULT_ENV_KEY, key)
    fernet = _get_fernet()
    assert isinstance(fernet, Fernet)


def test_get_fernet_no_key(monkeypatch):
    """Test that _get_fernet raises ValueError when no key is provided."""
    monkeypatch.delenv(_DEFAULT_ENV_KEY, raising=False)
    with pytest.raises(ValueError) as excinfo:
        _get_fernet()
    assert "Encryption key not provided" in str(excinfo.value)


def test_encrypt_decrypt_with_env_var(monkeypatch):
    """Test that encrypt_bytes and decrypt_bytes work with a key from the environment variable."""
    key = generate_key()
    monkeypatch.setenv(_DEFAULT_ENV_KEY, key)
    data = b"secret"
    token = encrypt_bytes(data)
    assert data != token
    plain = decrypt_bytes(token)
    assert plain == data


def test_decrypt_invalid_token():
    """Test that decrypt_bytes raises InvalidToken when given an invalid token."""
    key = generate_key()
    invalid_token = b"invalid token"

    with pytest.raises(InvalidToken):
        decrypt_bytes(invalid_token, key)


def test_decrypt_with_wrong_key():
    """Test that decrypt_bytes raises InvalidToken when given a valid token but the wrong key."""
    key1 = generate_key()
    key2 = generate_key()

    # Ensure we have different keys
    assert key1 != key2

    data = b"secret"
    token = encrypt_bytes(data, key1)

    # Trying to decrypt with the wrong key should raise InvalidToken
    with pytest.raises(InvalidToken):
        decrypt_bytes(token, key2)
