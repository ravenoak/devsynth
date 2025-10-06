import pytest
from pytest_bdd import scenarios

from .steps.test_webui_spec_editor_extended_steps import *  # noqa: F401,F403


pytestmark = [pytest.mark.fast]

scenarios("features/general/webui_spec_editor_extended.feature")
