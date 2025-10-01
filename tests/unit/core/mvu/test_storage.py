from __future__ import annotations

import pytest

from devsynth.core.mvu.models import MVUU
from devsynth.core.mvu.storage import append_mvuu_footer, format_mvuu_footer

pytestmark = [pytest.mark.fast]


def _sample_mvuu() -> MVUU:
    return MVUU(
        utility_statement="do",
        affected_files=["a.py"],
        tests=["test_a.py"],
        TraceID="DSY-1",
        mvuu=True,
        issue="ISSUE-1",
    )


def test_format_mvuu_footer_contains_json() -> None:
    footer = format_mvuu_footer(_sample_mvuu())
    assert footer.startswith("```json")
    assert '"TraceID": "DSY-1"' in footer


def test_append_mvuu_footer_appends_block() -> None:
    message = "feat: add feature"
    result = append_mvuu_footer(message, _sample_mvuu())
    assert '"TraceID": "DSY-1"' in result
    assert result.endswith("```\n")
