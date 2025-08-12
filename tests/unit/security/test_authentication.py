import pytest

from devsynth.exceptions import AuthenticationError
from devsynth.security.authentication import (
    authenticate,
    hash_password,
    verify_password,
)


@pytest.mark.medium
def test_hash_and_verify_password_succeeds():
    """Test that hash and verify password succeeds.

    ReqID: FR-61"""
    password = "Secret123!"
    hashed = hash_password(password)
    assert password not in hashed
    assert verify_password(hashed, password)
    assert not verify_password(hashed, "wrong")


@pytest.mark.medium
def test_authenticate_success_succeeds():
    """Test that authenticate success succeeds.

    ReqID: FR-61"""
    pwd = "password"
    creds = {"alice": hash_password(pwd)}
    assert authenticate("alice", pwd, creds)


@pytest.mark.medium
def test_authenticate_failure_succeeds():
    """Test that authenticate failure succeeds.

    ReqID: FR-61"""
    creds = {"bob": hash_password("password")}
    try:
        authenticate("bob", "bad", creds)
    except AuthenticationError:
        assert True
    else:
        assert False
