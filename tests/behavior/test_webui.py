import pytest
from pytest_bdd import scenarios

from .steps.webui_steps import *  # noqa: F401,F403


pytestmark = [pytest.mark.fast]

scenarios("features/general/webui.feature")
