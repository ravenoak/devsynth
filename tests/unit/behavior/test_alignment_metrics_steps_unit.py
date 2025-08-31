import importlib

import pytest

# Importing the module before calling ``metrics_fail`` ensures the monkeypatch
# targets the submodule rather than the function that is re-exported from the
# package ``devsynth.application.cli.commands``.
cmd = importlib.import_module("devsynth.application.cli.commands.alignment_metrics_cmd")
import sys

sys.modules["devsynth.application.cli.commands.alignment_metrics_cmd"] = cmd
from tests.behavior.steps.test_alignment_metrics_steps import metrics_fail


@pytest.mark.fast
def test_metrics_fail_patches_calculate(monkeypatch):
    metrics_fail(monkeypatch)
    with pytest.raises(Exception, match="metrics failure"):
        cmd.calculate_alignment_coverage([])
