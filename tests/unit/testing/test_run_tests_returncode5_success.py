import pytest

import devsynth.testing.run_tests as rt
from devsynth.testing.run_tests import run_tests


@pytest.mark.fast
@pytest.mark.requires_resource("codebase")
def test_single_pass_non_keyword_returncode_5_is_success(monkeypatch) -> None:
    """ReqID: TR-RT-10 — Return code 5 is success in single-pass non-keyword path.

    In the single-pass, non-keyword path (no speed_categories), pytest return
    code 5 (no tests collected) should be treated as success. This exercises
    the branch where we do not pre-collect node ids and simply pass a category
    expression to pytest via '-m'.
    """

    # Force the branch: speed_categories=None, no extra_marker or keyword filter,
    # parallel=False to avoid xdist flags.

    class FakePopen:
        def __init__(
            self, cmd, stdout=None, stderr=None, text=False, env=None
        ):  # noqa: ANN001
            # Ensure the '-m' category expression is present and no '-k' keyword filter
            assert "-m" in cmd, f"expected -m category expression in cmd: {cmd}"
            assert "-k" not in cmd, f"did not expect -k in cmd: {cmd}"
            # Simulate pytest exit code 5 (no tests collected)
            self.returncode = 5

        def communicate(self):
            return ("", "")

    monkeypatch.setattr(rt.subprocess, "Popen", FakePopen)

    success, output = run_tests(
        target="unit-tests",
        speed_categories=None,
        verbose=False,
        report=False,
        parallel=False,
        segment=False,
        maxfail=None,
        extra_marker=None,
    )

    assert success is True
    # output may be empty; the important part is that success=True
