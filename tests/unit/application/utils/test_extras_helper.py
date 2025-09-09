import re

import pytest

from devsynth.application.utils.extras import (
    require_optional_package,
    suggest_install_message,
)


@pytest.mark.fast
def test_suggest_install_message_with_extra():
    msg = suggest_install_message(
        extra_name="memory", packages=["chromadb"], context="ChromaDB memory store"
    )
    assert "chromadb" in msg
    assert "poetry install --extras memory" in msg
    assert "pip install 'devsynth[memory]'" in msg


@pytest.mark.fast
def test_suggest_install_message_without_extra():
    msg = suggest_install_message(
        extra_name=None, packages=["somepkg"], context="Some feature"
    )
    assert "somepkg" in msg
    assert "Install with: pip install somepkg" in msg


@pytest.mark.fast
def test_require_optional_package_wraps_importerror():
    try:
        raise ImportError("orig")
    except ImportError as e:
        wrapped = require_optional_package(
            e, extra_name="webui", packages=["nicegui"], context="Web UI"
        )
        assert isinstance(wrapped, ImportError)
        # cause preserved
        assert wrapped.__cause__ is e
        text = str(wrapped)
        assert "nicegui" in text
        assert "devsynth[webui]" in text
