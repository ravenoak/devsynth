# Strict mypy error inventory – 2025-10-02 run

- Command: `poetry run mypy --strict src/devsynth`
- Total errors: 366
- Memory: 361
- Third-Party Stubs: 5

| Module | Errors | Domain | Owner |
| --- | ---: | --- | --- |
| `src/devsynth/application/memory/__init__.py` | 6 | memory | Memory Systems – Chen Wu |
| `src/devsynth/application/memory/adapters/__init__.py` | 2 | memory | Memory Systems – Chen Wu |
| `src/devsynth/application/memory/adapters/chromadb_vector_adapter.py` | 4 | memory | Memory Systems – Chen Wu |
| `src/devsynth/application/memory/adapters/enhanced_graph_memory_adapter.py` | 59 | memory | Memory Systems – Chen Wu |
| `src/devsynth/application/memory/adapters/graph_memory_adapter.py` | 46 | memory | Memory Systems – Chen Wu |
| `src/devsynth/application/memory/adapters/s3_memory_adapter.py` | 2 | memory | Memory Systems – Chen Wu |
| `src/devsynth/application/memory/adapters/tinydb_memory_adapter.py` | 4 | memory | Memory Systems – Chen Wu |
| `src/devsynth/application/memory/adapters/vector_memory_adapter.py` | 1 | memory | Memory Systems – Chen Wu |
| `src/devsynth/application/memory/chromadb_store.py` | 43 | memory | Memory Systems – Chen Wu |
| `src/devsynth/application/memory/context_manager.py` | 3 | memory | Memory Systems – Chen Wu |
| `src/devsynth/application/memory/dto.py` | 6 | memory | Memory Systems – Chen Wu |
| `src/devsynth/application/memory/duckdb_store.py` | 7 | memory | Memory Systems – Chen Wu |
| `src/devsynth/application/memory/error_logger.py` | 3 | memory | Memory Systems – Chen Wu |
| `src/devsynth/application/memory/faiss_store.py` | 1 | memory | Memory Systems – Chen Wu |
| `src/devsynth/application/memory/fallback.py` | 22 | memory | Memory Systems – Chen Wu |
| `src/devsynth/application/memory/json_file_store.py` | 15 | memory | Memory Systems – Chen Wu |
| `src/devsynth/application/memory/kuzu_store.py` | 28 | memory | Memory Systems – Chen Wu |
| `src/devsynth/application/memory/lmdb_store.py` | 16 | memory | Memory Systems – Chen Wu |
| `src/devsynth/application/memory/memory_integration.py` | 8 | memory | Memory Systems – Chen Wu |
| `src/devsynth/application/memory/memory_manager.py` | 17 | memory | Memory Systems – Chen Wu |
| `src/devsynth/application/memory/metadata_serialization.py` | 1 | memory | Memory Systems – Chen Wu |
| `src/devsynth/application/memory/persistent_context_manager.py` | 2 | memory | Memory Systems – Chen Wu |
| `src/devsynth/application/memory/rdflib_store.py` | 5 | memory | Memory Systems – Chen Wu |
| `src/devsynth/application/memory/recovery.py` | 9 | memory | Memory Systems – Chen Wu |
| `src/devsynth/application/memory/retry.py` | 23 | memory | Memory Systems – Chen Wu |
| `src/devsynth/application/memory/sync_manager.py` | 23 | memory | Memory Systems – Chen Wu |
| `src/devsynth/application/memory/tinydb_store.py` | 3 | memory | Memory Systems – Chen Wu |
| `src/devsynth/application/memory/transaction_context.py` | 1 | memory | Memory Systems – Chen Wu |
| `src/devsynth/application/memory/vector_providers.py` | 1 | memory | Memory Systems – Chen Wu |
| `src/devsynth/application/memory/adapters/vector_memory_adapter.py` | 1 | third-party stubs | Hygiene WG |
| `src/devsynth/application/memory/faiss_store.py` | 2 | third-party stubs | Hygiene WG |
| `src/devsynth/application/memory/lmdb_store.py` | 1 | third-party stubs | Hygiene WG |
| `src/devsynth/application/memory/rdflib_store.py` | 1 | third-party stubs | Hygiene WG |
