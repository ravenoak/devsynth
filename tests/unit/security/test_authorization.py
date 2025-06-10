from devsynth.security.authorization import is_authorized, require_authorization
from devsynth.exceptions import AuthorizationError


ACL = {"admin": ["read", "write"], "user": ["read"]}


def test_is_authorized_true():
    assert is_authorized(["admin"], "write", ACL)


def test_is_authorized_false():
    assert not is_authorized(["user"], "write", ACL)


def test_require_authorization_raises():
    try:
        require_authorization(["user"], "write", ACL)
    except AuthorizationError:
        assert True
    else:
        assert False
