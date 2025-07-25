from devsynth.security.authentication import hash_password, verify_password


def test_argon2_hash_roundtrip():
    password = "S3cret!"
    hashed = hash_password(password)
    assert hashed.startswith("$argon2")
    assert verify_password(hashed, password)
