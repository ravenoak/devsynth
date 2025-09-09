import builtins
import os

import pytest

from devsynth.application.cli.commands.security_audit_cmd import (
    check_required_env,
    run_secrets_scan,
    security_audit_cmd,
)


@pytest.mark.fast
def test_check_required_env_raises_when_missing_env(monkeypatch):
    monkeypatch.delenv("DEVSYNTH_ACCESS_TOKEN", raising=False)
    with pytest.raises(RuntimeError) as exc:
        check_required_env()
    assert "Missing required environment variables" in str(exc.value)


@pytest.mark.fast
def test_security_audit_cmd_happy_path_with_skips(monkeypatch):
    # Ensure required env present
    monkeypatch.setenv("DEVSYNTH_ACCESS_TOKEN", "token123")

    # Stub out audit functions to avoid running tools
    class DummyAudit:
        def run_safety(self):
            called["safety"] = True

        def run_bandit(self):
            called["bandit"] = True

    called = {"safety": False, "bandit": False}

    # Patch module's audit reference
    import devsynth.application.cli.commands.security_audit_cmd as mod

    monkeypatch.setattr(mod, "audit", DummyAudit())

    # Skip all heavy checks so function mainly exercises flow
    security_audit_cmd(
        skip_static=True, skip_safety=True, skip_secrets=True, skip_owasp=True
    )

    # Since we skipped, these should still be False
    assert called["safety"] is False
    assert called["bandit"] is False


@pytest.mark.fast
def test_security_audit_runs_when_not_skipped(monkeypatch):
    monkeypatch.setenv("DEVSYNTH_ACCESS_TOKEN", "token123")

    flags = {"safety": False, "bandit": False}

    class DummyAudit:
        def run_safety(self):
            flags["safety"] = True

        def run_bandit(self):
            flags["bandit"] = True

    import devsynth.application.cli.commands.security_audit_cmd as mod

    monkeypatch.setattr(mod, "audit", DummyAudit())

    # Also skip secrets/owasp to avoid file and subprocess scanning
    security_audit_cmd(
        skip_static=False, skip_safety=False, skip_secrets=True, skip_owasp=True
    )

    assert flags == {"safety": True, "bandit": True}


@pytest.mark.fast
def test_run_secrets_scan_detects_simple_pattern(tmp_path, monkeypatch):
    # Create a temp file with a mock secret pattern
    data = "api_key: 'ABCDEFGHIJKLMNOP'\nno secret here\n"
    p = tmp_path / "config.yaml"
    p.write_text(data)

    # Run in the tmp directory
    monkeypatch.chdir(tmp_path)

    with pytest.raises(RuntimeError) as exc:
        run_secrets_scan()
    msg = str(exc.value)
    assert "Potential secrets detected" in msg
    assert "config.yaml" in msg
