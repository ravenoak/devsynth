from __future__ import annotations

from collections.abc import MutableMapping
from collections.abc import Callable

import pytest

import devsynth.testing.run_tests as rt

pytestmark = pytest.mark.fast


@pytest.mark.parametrize(
    ("ensure", "initial_env", "expected_changed", "expected_addopts"),
    (
        (
            rt.ensure_pytest_cov_plugin_env,
            {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTEST_ADDOPTS": "--no-cov -s"},
            False,
            "--no-cov -s",
        ),
        (
            rt.ensure_pytest_cov_plugin_env,
            {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTEST_ADDOPTS": "-k smoke"},
            True,
            "-k smoke -p pytest_cov",
        ),
        (
            rt.ensure_pytest_bdd_plugin_env,
            {
                "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
                "PYTEST_ADDOPTS": "-p no:pytest_bdd -s",
            },
            False,
            "-p no:pytest_bdd -s",
        ),
        (
            rt.ensure_pytest_bdd_plugin_env,
            {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTEST_ADDOPTS": "-k feature"},
            True,
            "-k feature -p pytest_bdd.plugin",
        ),
    ),
)
def test_ensure_pytest_plugin_env_addopts_overrides(
    ensure: Callable[[MutableMapping[str, str]], bool],
    initial_env: dict[str, str],
    expected_changed: bool,
    expected_addopts: str,
) -> None:
    """Ensure pytest plugin helpers respect opt-outs and reinject when needed."""

    env: dict[str, str] = dict(initial_env)

    changed = ensure(env)

    assert changed is expected_changed
    assert env["PYTEST_ADDOPTS"] == expected_addopts

    if not expected_changed:
        assert env == initial_env
    else:
        assert env != initial_env
        assert env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
