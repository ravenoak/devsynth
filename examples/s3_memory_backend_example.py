"""Example using the S3 memory backend."""

import os

from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.memory import MemoryType

# Configure backend via environment variables
os.environ.setdefault("DEVSYNTH_MEMORY_STORE", "s3")
os.environ.setdefault("DEVSYNTH_S3_BUCKET", "devsynth-example")

# In a real deployment the bucket must already exist and AWS credentials must be
# configured.  This example focuses on the MemoryManager API.
manager = MemoryManager()
item_id = manager.store_with_edrr_phase("example", MemoryType.CODE, "EXPAND")
print(manager.retrieve(item_id))
