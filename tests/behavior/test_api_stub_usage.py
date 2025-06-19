from pytest_bdd import scenarios

from .steps.api_stub_steps import *  # noqa: F401,F403

scenarios("features/api_stub_usage.feature")
