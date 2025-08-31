import pytest

from devsynth.exceptions import AuthorizationError
from devsynth.security.authorization import require_authorization

ACL = {"admin": ["read", "write"], "user": ["read"]}


@pytest.mark.fast
def test_require_authorization_allows_authorized_action():
    require_authorization(["admin"], "write", ACL)


@pytest.mark.fast
def test_require_authorization_raises_forbidden():
    with pytest.raises(AuthorizationError):
        require_authorization(["user"], "write", ACL)
