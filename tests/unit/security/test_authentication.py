from devsynth.security.authentication import hash_password, verify_password, authenticate
from devsynth.exceptions import AuthenticationError


def test_hash_and_verify_password_succeeds():
    """Test that hash and verify password succeeds.

ReqID: N/A"""
    password = 'Secret123!'
    hashed = hash_password(password)
    assert password not in hashed
    assert verify_password(hashed, password)
    assert not verify_password(hashed, 'wrong')


def test_authenticate_success_succeeds():
    """Test that authenticate success succeeds.

ReqID: N/A"""
    pwd = 'password'
    creds = {'alice': hash_password(pwd)}
    assert authenticate('alice', pwd, creds)


def test_authenticate_failure_succeeds():
    """Test that authenticate failure succeeds.

ReqID: N/A"""
    creds = {'bob': hash_password('password')}
    try:
        authenticate('bob', 'bad', creds)
    except AuthenticationError:
        assert True
    else:
        assert False
