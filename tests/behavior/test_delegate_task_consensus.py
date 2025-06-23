from pytest_bdd import scenarios

from .steps.delegate_task_consensus_steps import *  # noqa: F401,F403

scenarios("features/delegate_task_consensus.feature")
