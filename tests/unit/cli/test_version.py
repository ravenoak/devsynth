import pytest

from devsynth.adapters.cli import typer_adapter as adapter
from devsynth import __version__


@pytest.mark.fast
def test_cli_version_option_prints_version_and_exits_zero(capsys):
    with pytest.raises(SystemExit) as exc:
        adapter.parse_args(["--version"])  # triggers eager option
    assert exc.value.code == 0
    out = capsys.readouterr().out.strip()
    assert __version__ in out
