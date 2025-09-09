import os

import pytest

from devsynth.security import deployment as secdeploy


@pytest.mark.fast
def test_require_non_root_user_noop_without_flag(monkeypatch):
    """require_non_root_user is a no-op when flag not set.

    ReqID: SEC-01"""
    monkeypatch.delenv("DEVSYNTH_REQUIRE_NON_ROOT", raising=False)
    monkeypatch.setattr(os, "geteuid", lambda: 0)
    secdeploy.require_non_root_user()


@pytest.mark.fast
def test_require_non_root_user_raises_for_root(monkeypatch):
    """require_non_root_user raises when running as root.

    ReqID: SEC-02"""
    monkeypatch.setenv("DEVSYNTH_REQUIRE_NON_ROOT", "true")
    monkeypatch.setattr(os, "geteuid", lambda: 0)
    with pytest.raises(RuntimeError):
        secdeploy.require_non_root_user()


@pytest.mark.fast
def test_check_required_env_vars(monkeypatch):
    """check_required_env_vars enforces presence of variables.

    ReqID: SEC-03"""
    monkeypatch.delenv("FOO", raising=False)
    with pytest.raises(RuntimeError):
        secdeploy.check_required_env_vars(["FOO"])
    monkeypatch.setenv("FOO", "1")
    secdeploy.check_required_env_vars(["FOO"])


@pytest.mark.fast
def test_apply_secure_umask(monkeypatch):
    """apply_secure_umask sets restrictive mask and returns previous.

    ReqID: SEC-04"""
    called = {}

    def fake_umask(mask):
        called["mask"] = mask
        return 0o022

    monkeypatch.setattr(os, "umask", fake_umask)
    prev = secdeploy.apply_secure_umask()
    assert prev == 0o022
    assert called["mask"] == 0o077


@pytest.mark.fast
def test_harden_runtime_invokes_helpers(monkeypatch):
    """harden_runtime calls helper functions.

    ReqID: SEC-05"""
    calls = {}
    monkeypatch.setenv("FOO", "1")
    monkeypatch.setattr(
        secdeploy, "require_non_root_user", lambda: calls.setdefault("non_root", True)
    )
    monkeypatch.setattr(
        secdeploy, "apply_secure_umask", lambda: calls.setdefault("umask", True)
    )

    def fake_check(names):
        calls["required_env"] = list(names)

    monkeypatch.setattr(secdeploy, "check_required_env_vars", fake_check)
    secdeploy.harden_runtime(["FOO"])
    assert calls["non_root"]
    assert calls["umask"]
    assert calls["required_env"] == ["FOO"]


@pytest.mark.fast
def test_harden_runtime_raises_when_env_missing(monkeypatch):
    """harden_runtime propagates missing env variable errors.

    ReqID: SEC-06"""
    monkeypatch.delenv("MISSING", raising=False)
    monkeypatch.setattr(
        secdeploy, "apply_secure_umask", lambda: (_ for _ in ()).throw(AssertionError)
    )
    monkeypatch.setattr(
        secdeploy,
        "require_non_root_user",
        lambda: (_ for _ in ()).throw(AssertionError),
    )
    with pytest.raises(RuntimeError):
        secdeploy.harden_runtime(["MISSING"])
