from pytest_bdd import scenarios

from .steps.delegate_task_steps import *  # noqa: F401,F403

scenarios("features/delegate_task.feature")
