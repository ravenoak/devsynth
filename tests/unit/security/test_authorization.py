import pytest

from devsynth.exceptions import AuthorizationError
from devsynth.security.authorization import is_authorized, require_authorization

ACL = {"admin": ["read", "write"], "user": ["read"], "superuser": ["*"]}
EMPTY_ACL = {}
CASE_SENSITIVE_ACL = {"Admin": ["Read", "Write"], "user": ["read"]}


@pytest.mark.medium
def test_is_authorized_true_returns_expected_result():
    """Test that is_authorized returns True when the user has the required role.

    ReqID: FR-62"""
    assert is_authorized(["admin"], "write", ACL)


@pytest.mark.medium
def test_is_authorized_false_returns_expected_result():
    """Test that is_authorized returns False when the user doesn't have the required role.

    ReqID: FR-62"""
    assert not is_authorized(["user"], "write", ACL)


@pytest.mark.medium
def test_is_authorized_multiple_roles_succeeds():
    """Test that is_authorized works with multiple roles.

    ReqID: FR-62"""
    assert is_authorized(["user", "admin"], "write", ACL)
    assert is_authorized(["guest", "user"], "read", ACL)
    assert not is_authorized(["guest", "user"], "delete", ACL)


@pytest.mark.medium
def test_is_authorized_wildcard_succeeds():
    """Test that is_authorized works with wildcard actions.

    ReqID: FR-62"""
    assert is_authorized(["superuser"], "read", ACL)
    assert is_authorized(["superuser"], "write", ACL)
    assert is_authorized(["superuser"], "delete", ACL)


@pytest.mark.medium
def test_is_authorized_role_not_in_acl_returns_expected_result():
    """Test that is_authorized returns False when the role doesn't exist in the ACL.

    ReqID: FR-62"""
    assert not is_authorized(["guest"], "read", ACL)
    assert not is_authorized(["unknown"], "write", ACL)


@pytest.mark.medium
def test_is_authorized_empty_roles_returns_expected_result():
    """Test that is_authorized returns False when the user has no roles.

    ReqID: FR-62"""
    assert not is_authorized([], "read", ACL)
    assert not is_authorized([], "write", ACL)


@pytest.mark.medium
def test_is_authorized_empty_acl_returns_expected_result():
    """Test that is_authorized returns False when the ACL is empty.

    ReqID: FR-62"""
    assert not is_authorized(["admin"], "read", EMPTY_ACL)
    assert not is_authorized(["user"], "write", EMPTY_ACL)


@pytest.mark.medium
def test_is_authorized_case_sensitivity_succeeds():
    """Test that is_authorized is case-sensitive for roles and actions.

    ReqID: FR-62"""
    assert not is_authorized(["Admin"], "write", ACL)
    assert is_authorized(["Admin"], "Write", CASE_SENSITIVE_ACL)
    assert not is_authorized(["admin"], "Write", ACL)
    assert is_authorized(["Admin"], "Write", CASE_SENSITIVE_ACL)
    assert not is_authorized(["user"], "Read", ACL)


@pytest.mark.medium
def test_is_authorized_iterable_roles_succeeds():
    """Test that is_authorized works with different iterable types for roles.

    ReqID: FR-62"""
    assert is_authorized(["admin"], "write", ACL)
    assert is_authorized(("admin",), "write", ACL)
    assert is_authorized({"admin"}, "write", ACL)

    class RolesIterable:

        def __iter__(self):
            return iter(["admin"])

    assert is_authorized(RolesIterable(), "write", ACL)


@pytest.mark.medium
def test_require_authorization_raises():
    """Test that require_authorization raises an AuthorizationError when the user doesn't have the required role.

    ReqID: FR-62"""
    with pytest.raises(AuthorizationError) as excinfo:
        require_authorization(["user"], "write", ACL)
    assert excinfo.value.message == "Permission denied"
    assert excinfo.value.details["roles"] == ["user"]
    assert excinfo.value.details["action"] == "write"


@pytest.mark.medium
def test_require_authorization_no_exception_raises_error():
    """Test that require_authorization doesn't raise an exception when the user is authorized.

    ReqID: FR-62"""
    require_authorization(["admin"], "write", ACL)
    require_authorization(["user"], "read", ACL)
    require_authorization(["superuser"], "delete", ACL)


@pytest.mark.medium
def test_require_authorization_empty_roles_raises_error():
    """Test that require_authorization raises an AuthorizationError when the user has no roles.

    ReqID: FR-62"""
    with pytest.raises(AuthorizationError) as excinfo:
        require_authorization([], "read", ACL)
    assert excinfo.value.message == "Permission denied"
    assert excinfo.value.details["roles"] == []
    assert excinfo.value.details["action"] == "read"


@pytest.mark.medium
def test_require_authorization_empty_acl_raises_error():
    """Test that require_authorization raises an AuthorizationError when the ACL is empty.

    ReqID: FR-62"""
    with pytest.raises(AuthorizationError) as excinfo:
        require_authorization(["admin"], "read", EMPTY_ACL)
    assert excinfo.value.message == "Permission denied"
    assert excinfo.value.details["roles"] == ["admin"]
    assert excinfo.value.details["action"] == "read"
