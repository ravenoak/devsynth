import importlib

import pytest


@pytest.mark.fast
def test_argparser_includes_cross_check_flag():
    mod = importlib.import_module("scripts.verify_test_markers")
    parser = mod.get_arg_parser()
    help_text = parser.format_help()
    assert "--cross-check-collection" in help_text
