from devsynth.security.encryption import generate_key, encrypt_bytes, decrypt_bytes


def test_encrypt_decrypt_roundtrip():
    key = generate_key()
    data = b"secret"
    token = encrypt_bytes(data, key)
    assert data != token
    plain = decrypt_bytes(token, key)
    assert plain == data
