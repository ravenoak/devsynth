import base64
import os

import pytest

from devsynth.security import authentication as auth_mod
from devsynth.security.authentication import hash_password, verify_password
from devsynth.security.encryption import decrypt_bytes, encrypt_bytes, generate_key


class TestArgon2Defaults:
    @pytest.mark.fast
    def test_password_hasher_parameters_safe_defaults(self):
        # Validate that our PasswordHasher was configured with explicit safe defaults
        hasher = auth_mod._password_hasher  # internal by design; verify configuration
        assert hasher.time_cost >= 3
        assert hasher.memory_cost >= 65536
        assert hasher.parallelism >= 1
        assert hasher.hash_len >= 32
        assert hasher.salt_len >= 16

    @pytest.mark.fast
    def test_hash_and_verify_roundtrip(self):
        h = hash_password("s3cur3")
        assert verify_password(h, "s3cur3") is True
        assert verify_password(h, "wrong") is False


class TestFernetKeyValidation:
    @pytest.mark.fast
    def test_generate_key_validates_and_encrypts(self, monkeypatch):
        key = generate_key()
        # Should be base64 urlsafe and decode to 32 bytes
        decoded = base64.urlsafe_b64decode(key.encode())
        assert len(decoded) == 32
        # Roundtrip encrypt/decrypt
        data = b"hello"
        token = encrypt_bytes(data, key)
        out = decrypt_bytes(token, key)
        assert out == data

    @pytest.mark.fast
    def test_invalid_key_rejected(self, monkeypatch):
        os.environ.pop("DEVSYNTH_ENCRYPTION_KEY", None)
        # 32-byte raw -> base64 then trim last char to break padding/length
        bad_key = base64.urlsafe_b64encode(b"x" * 31).decode()
        with pytest.raises(ValueError):
            encrypt_bytes(b"x", bad_key)

    @pytest.mark.fast
    def test_missing_key_env_raises(self, monkeypatch):
        monkeypatch.delenv("DEVSYNTH_ENCRYPTION_KEY", raising=False)
        with pytest.raises(ValueError):
            encrypt_bytes(b"x")
