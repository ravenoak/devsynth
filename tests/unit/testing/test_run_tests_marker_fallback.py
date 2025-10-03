"""Regression coverage for marker fallback and segmentation bypass."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

import devsynth.testing.run_tests as rt


@pytest.mark.fast
def test_run_tests_marker_fallback_skips_segmentation(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """When no nodes match, run_tests should fall back without segmenting."""

    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "ensure_pytest_cov_plugin_env", lambda env: False)
    monkeypatch.setattr(rt, "ensure_pytest_bdd_plugin_env", lambda env: False)

    monkeypatch.setattr(rt, "collect_tests_with_cache", lambda *args, **kwargs: [])

    segmented_calls: list[dict[str, Any]] = []
    monkeypatch.setattr(
        rt,
        "_run_segmented_tests",
        lambda **kwargs: segmented_calls.append(kwargs) or (True, "segment")
    )

    batch_calls: list[list[str]] = []

    def fake_batch(**kwargs: Any) -> tuple[bool, str]:
        batch_calls.append(kwargs.get("node_ids", []))
        return True, "batch success"

    monkeypatch.setattr(rt, "_run_single_test_batch", fake_batch)

    success, output = rt.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        segment=True,
        report=False,
        verbose=False,
        parallel=False,
    )

    assert success is True
    assert output.startswith("Marker fallback executed.")
    assert not segmented_calls, "segmentation should be bypassed when fallback triggers"
    assert batch_calls == [[rt.TARGET_PATHS["unit-tests"]]]
