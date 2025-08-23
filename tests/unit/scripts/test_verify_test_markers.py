from pathlib import Path

import pytest

from scripts import verify_test_markers as vtm


@pytest.mark.fast
def test_verify_test_markers_cache(tmp_path: Path) -> None:
    """Cache hit/miss behavior. ReqID: QA-01"""
    test_file = tmp_path / "test_sample.py"
    test_file.write_text(
        "import pytest\n\n@pytest.mark.fast\ndef test_one():\n    assert True\n",
        encoding="utf-8",
    )

    vtm.PERSISTENT_CACHE.clear()
    vtm.FILE_HASHES.clear()

    result1 = vtm.verify_directory_markers(str(tmp_path))
    assert result1["cache_misses"] == 1
    assert result1["cache_hits"] == 0

    result2 = vtm.verify_directory_markers(str(tmp_path))
    assert result2["cache_hits"] == 1
    assert result2["cache_misses"] == 0


@pytest.mark.fast
def test_verify_test_markers_collection_error(tmp_path: Path) -> None:
    """Reports collection errors. ReqID: QA-02"""
    test_file = tmp_path / "test_bad.py"
    test_file.write_text(
        "import pytest\nimport nonexistent_module\n\n@pytest.mark.fast\ndef test_fail():\n    pass\n",
        encoding="utf-8",
    )

    vtm.PERSISTENT_CACHE.clear()
    vtm.FILE_HASHES.clear()

    result = vtm.verify_directory_markers(str(tmp_path))
    assert result["files_with_issues"] == 1
    file_result = result["files"][str(test_file)]
    assert any(issue["type"] == "collection_error" for issue in file_result["issues"])
    assert result["collection_errors"]
