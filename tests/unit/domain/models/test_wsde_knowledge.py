from types import SimpleNamespace

import pytest

from devsynth.domain.models.wsde_knowledge import (
    _get_task_id,
    _identify_relevant_knowledge,
)


@pytest.mark.fast
def test_get_task_id_uses_existing_id():
    """ReqID: WSDE-KNOW-01 — uses existing task id when provided."""
    task = {"id": "task-123", "description": "Do something"}
    assert _get_task_id(SimpleNamespace(), task) == "task-123"


@pytest.mark.fast
def test_identify_relevant_knowledge_matches_keywords():
    """ReqID: WSDE-KNOW-02 — matches external knowledge by keywords."""
    task = {"description": "Build web api"}
    solution = {"content": "Use Flask"}
    external = {
        "standards": [{"name": "Flask Standard", "keywords": ["flask"]}],
        "best_practices": [{"name": "API Guide", "keywords": ["api"]}],
        "patterns": [{"name": "MVC", "keywords": ["flask"]}],
        "domains": {"web": {"keywords": ["web"]}},
    }
    result = _identify_relevant_knowledge(SimpleNamespace(), task, solution, external)
    assert external["standards"][0] in result["standards"]
    assert external["best_practices"][0] in result["best_practices"]
    assert external["patterns"][0] in result["patterns"]
    assert "web" in result["domain_specific"]
