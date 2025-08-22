import pytest

from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.memory import MemoryType

pytest.importorskip("boto3")
pytest.importorskip("moto")
from moto import mock_s3


@pytest.mark.fast
def test_memory_manager_selects_s3_backend(monkeypatch):
    """Ensure MemoryManager uses the S3 adapter when configured. ReqID: additional-storage-backends-1"""
    import boto3

    bucket = "devsynth-test"
    monkeypatch.setenv("DEVSYNTH_MEMORY_STORE", "s3")
    monkeypatch.setenv("DEVSYNTH_S3_BUCKET", bucket)

    with mock_s3():
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket=bucket)

        manager = MemoryManager()
        assert "s3" in manager.adapters

        item_id = manager.store_with_edrr_phase("data", MemoryType.CODE, "EXPAND")
        retrieved = manager.retrieve(item_id)
        assert retrieved and retrieved.content == "data"
