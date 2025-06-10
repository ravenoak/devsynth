from devsynth.security.authentication import (
    hash_password,
    verify_password,
    authenticate,
)
from devsynth.exceptions import AuthenticationError


def test_hash_and_verify_password():
    password = "Secret123!"
    hashed = hash_password(password)
    assert password not in hashed
    assert verify_password(hashed, password)
    assert not verify_password(hashed, "wrong")


def test_authenticate_success():
    pwd = "password"
    creds = {"alice": hash_password(pwd)}
    assert authenticate("alice", pwd, creds)


def test_authenticate_failure():
    creds = {"bob": hash_password("password")}
    try:
        authenticate("bob", "bad", creds)
    except AuthenticationError:
        assert True
    else:
        assert False
