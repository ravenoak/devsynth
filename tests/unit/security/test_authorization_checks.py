import pytest
from devsynth.security.authorization import require_authorization
from devsynth.exceptions import AuthorizationError

ACL = {"admin": ["read", "write"], "user": ["read"]}


def test_require_authorization_allows_authorized_action():
    require_authorization(["admin"], "write", ACL)


def test_require_authorization_raises_forbidden():
    with pytest.raises(AuthorizationError):
        require_authorization(["user"], "write", ACL)
