"""Step definitions for doctor_missing_env.feature."""

from pytest_bdd import scenarios, given, then

scenarios("../features/doctor_missing_env.feature")


@given("essential environment variables are missing")
def missing_env_vars(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LM_STUDIO_ENDPOINT", raising=False)


@then("the output should mention the missing variables")
def output_mentions_missing_vars(command_context):
    output = command_context.get("output", "")
    assert "OPENAI_API_KEY" in output or "LM_STUDIO_ENDPOINT" in output
