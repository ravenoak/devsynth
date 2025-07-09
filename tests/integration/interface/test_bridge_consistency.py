import inspect
import html
import re
from unittest.mock import MagicMock
import pytest
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.agentapi import APIBridge
from devsynth.interface.webui_bridge import WebUIBridge
from devsynth.interface.ux_bridge import UXBridge


def _sanitize(text: str) ->str:
    text = re.sub('<script.*?>.*?</script>', '', text, flags=re.IGNORECASE |
        re.DOTALL)
    text = re.sub('[\\x00-\\x1f\\x7f]', '', text)
    return html.escape(text.strip())


def _init_cmd(*, bridge):
    value = bridge.ask_question('val?')
    bridge.display_result(value)


def test_bridge_output_consistency_succeeds(monkeypatch):
    """Test that bridge output consistency succeeds.

ReqID: N/A"""
    raw_input = '<script>alert(1)</script><b>demo</b>'
    expected = _sanitize(raw_input)
    out = MagicMock()
    monkeypatch.setattr('devsynth.interface.cli.Prompt.ask', lambda *a, **k:
        raw_input)
    monkeypatch.setattr('devsynth.interface.cli.validate_safe_input', lambda
        x: x)
    monkeypatch.setattr('rich.console.Console.print', out)
    cli_bridge = CLIUXBridge()
    _init_cmd(bridge=cli_bridge)
    cli_result = out.call_args.args[0]
    web_bridge = WebUIBridge()
    monkeypatch.setattr(web_bridge, 'ask_question', lambda *a, **k: raw_input)
    _init_cmd(bridge=web_bridge)
    web_result = web_bridge.messages[0]
    api_bridge = APIBridge([raw_input])
    _init_cmd(bridge=api_bridge)
    api_result = api_bridge.messages[0]
    assert cli_result == web_result == api_result == expected


def test_bridge_method_signatures_succeeds():
    """Test that bridge method signatures succeeds.

ReqID: N/A"""
    classes = [CLIUXBridge, APIBridge, WebUIBridge]
    methods = ['ask_question', 'confirm_choice', 'display_result',
        'create_progress']
    for method in methods:
        base_sig = inspect.signature(getattr(UXBridge, method))
        for cls in classes:
            impl_sig = inspect.signature(getattr(cls, method))
            assert list(impl_sig.parameters.keys()) == list(base_sig.
                parameters.keys())
