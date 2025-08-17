import pytest

from devsynth.application.cli.commands import security_audit_cmd as cmd


class DummyBridge:
    def display_result(self, *_args, **_kwargs) -> None:  # pragma: no cover - trivial
        pass


@pytest.mark.fast
def test_security_audit_cmd_runs_checks(monkeypatch):
    """Command should invoke bandit and dependency scans."""
    monkeypatch.setenv("DEVSYNTH_ACCESS_TOKEN", "token")
    called = {}
    monkeypatch.setattr(
        cmd.audit, "run_bandit", lambda: called.setdefault("bandit", True)
    )
    monkeypatch.setattr(
        cmd.audit, "run_safety", lambda: called.setdefault("safety", True)
    )

    cmd.security_audit_cmd(skip_secrets=True, skip_owasp=True, bridge=DummyBridge())

    assert called == {"bandit": True, "safety": True}


@pytest.mark.fast
def test_security_audit_cmd_respects_skip_flags(monkeypatch):
    """Skipping flags should avoid running checks."""
    monkeypatch.setenv("DEVSYNTH_ACCESS_TOKEN", "token")
    called = {}
    monkeypatch.setattr(
        cmd.audit, "run_bandit", lambda: called.setdefault("bandit", True)
    )
    monkeypatch.setattr(
        cmd.audit, "run_safety", lambda: called.setdefault("safety", True)
    )

    cmd.security_audit_cmd(
        skip_static=True,
        skip_safety=True,
        skip_secrets=True,
        skip_owasp=True,
        bridge=DummyBridge(),
    )

    assert called == {}


@pytest.mark.fast
def test_security_audit_cmd_registered():
    """The security-audit command should be available via the CLI registry."""
    # Import extra_cmds to ensure registration side effects run
    import devsynth.application.cli.commands.extra_cmds  # noqa: F401
    from devsynth.application.cli.registry import COMMAND_REGISTRY

    assert COMMAND_REGISTRY.get("security-audit") is cmd.security_audit_cmd
