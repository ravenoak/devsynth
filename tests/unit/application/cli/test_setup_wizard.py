from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[4]
    / "src"
    / "devsynth"
    / "application"
    / "cli"
    / "setup_wizard.py"
)
spec = spec_from_file_location("setup_wizard", MODULE_PATH)
setup_wizard = module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(setup_wizard)
SetupWizard = setup_wizard.SetupWizard


def test_setup_wizard_instantiation() -> None:
    wizard = SetupWizard()
    assert isinstance(wizard, SetupWizard)
