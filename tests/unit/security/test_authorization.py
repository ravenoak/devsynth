import pytest
from devsynth.security.authorization import is_authorized, require_authorization
from devsynth.exceptions import AuthorizationError


ACL = {"admin": ["read", "write"], "user": ["read"], "superuser": ["*"]}
EMPTY_ACL = {}
CASE_SENSITIVE_ACL = {"Admin": ["Read", "Write"], "user": ["read"]}


def test_is_authorized_true():
    """Test that is_authorized returns True when the user has the required role."""
    assert is_authorized(["admin"], "write", ACL)


def test_is_authorized_false():
    """Test that is_authorized returns False when the user doesn't have the required role."""
    assert not is_authorized(["user"], "write", ACL)


def test_is_authorized_multiple_roles():
    """Test that is_authorized works with multiple roles."""
    assert is_authorized(["user", "admin"], "write", ACL)
    assert is_authorized(["guest", "user"], "read", ACL)
    assert not is_authorized(["guest", "user"], "delete", ACL)


def test_is_authorized_wildcard():
    """Test that is_authorized works with wildcard actions."""
    assert is_authorized(["superuser"], "read", ACL)
    assert is_authorized(["superuser"], "write", ACL)
    assert is_authorized(["superuser"], "delete", ACL)


def test_is_authorized_role_not_in_acl():
    """Test that is_authorized returns False when the role doesn't exist in the ACL."""
    assert not is_authorized(["guest"], "read", ACL)
    assert not is_authorized(["unknown"], "write", ACL)


def test_is_authorized_empty_roles():
    """Test that is_authorized returns False when the user has no roles."""
    assert not is_authorized([], "read", ACL)
    assert not is_authorized([], "write", ACL)


def test_is_authorized_empty_acl():
    """Test that is_authorized returns False when the ACL is empty."""
    assert not is_authorized(["admin"], "read", EMPTY_ACL)
    assert not is_authorized(["user"], "write", EMPTY_ACL)


def test_is_authorized_case_sensitivity():
    """Test that is_authorized is case-sensitive for roles and actions."""
    # Role case sensitivity
    assert not is_authorized(["Admin"], "write", ACL)  # "Admin" != "admin"
    assert is_authorized(["Admin"], "Write", CASE_SENSITIVE_ACL)  # Exact match

    # Action case sensitivity
    assert not is_authorized(["admin"], "Write", ACL)  # "Write" != "write"
    assert is_authorized(["Admin"], "Write", CASE_SENSITIVE_ACL)  # Exact match
    assert not is_authorized(["user"], "Read", ACL)  # "Read" != "read"


def test_is_authorized_iterable_roles():
    """Test that is_authorized works with different iterable types for roles."""
    # List
    assert is_authorized(["admin"], "write", ACL)

    # Tuple
    assert is_authorized(("admin",), "write", ACL)

    # Set
    assert is_authorized({"admin"}, "write", ACL)

    # Custom iterable
    class RolesIterable:
        def __iter__(self):
            return iter(["admin"])

    assert is_authorized(RolesIterable(), "write", ACL)


def test_require_authorization_raises():
    """Test that require_authorization raises an AuthorizationError when the user doesn't have the required role."""
    with pytest.raises(AuthorizationError) as excinfo:
        require_authorization(["user"], "write", ACL)

    assert excinfo.value.message == "Permission denied"
    assert excinfo.value.details["roles"] == ["user"]
    assert excinfo.value.details["action"] == "write"


def test_require_authorization_no_exception():
    """Test that require_authorization doesn't raise an exception when the user is authorized."""
    # Should not raise an exception
    require_authorization(["admin"], "write", ACL)
    require_authorization(["user"], "read", ACL)
    require_authorization(["superuser"], "delete", ACL)


def test_require_authorization_empty_roles():
    """Test that require_authorization raises an AuthorizationError when the user has no roles."""
    with pytest.raises(AuthorizationError) as excinfo:
        require_authorization([], "read", ACL)

    assert excinfo.value.message == "Permission denied"
    assert excinfo.value.details["roles"] == []
    assert excinfo.value.details["action"] == "read"


def test_require_authorization_empty_acl():
    """Test that require_authorization raises an AuthorizationError when the ACL is empty."""
    with pytest.raises(AuthorizationError) as excinfo:
        require_authorization(["admin"], "read", EMPTY_ACL)

    assert excinfo.value.message == "Permission denied"
    assert excinfo.value.details["roles"] == ["admin"]
    assert excinfo.value.details["action"] == "read"
