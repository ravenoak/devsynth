---
title: "Memory Integration Guide"
date: "2025-08-05"
version: "0.1.0a1"
tags:
  - "developer-guide"
  - "guide"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-08-05"
---

# Memory Integration Guide

This guide provides detailed information on the DevSynth memory integration system, including its architecture, common issues, and best practices for implementing robust cross-store operations.

See [Kuzu Memory Integration feature](../features/kuzu_memory_integration.md) for details on the Kuzu backend.

## Table of Contents

- [Overview](#overview)
- [Memory System Architecture](#memory-system-architecture)
- [Memory Adapters](#memory-adapters)
- [Cross-Store Operations](#cross-store-operations)
- [Transaction Support](#transaction-support)
- [Error Handling and Recovery](#error-handling-and-recovery)
- [Fallback Mechanisms](#fallback-mechanisms)
- [Testing Memory Integration](#testing-memory-integration)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Reference](#reference)

## Overview

The DevSynth memory system provides a unified interface for storing and retrieving different types of memory items across various storage backends. It supports cross-store operations, allowing data to be synchronized between different storage backends and enabling complex queries that span multiple stores.

Key components of the memory integration system include:

1. **Memory Manager**: Provides a unified interface to different memory adapters
2. **Memory Adapters**: Implement storage-specific operations for different backends
3. **Sync Manager**: Handles synchronization between different memory stores
4. **Query Router**: Routes queries to appropriate memory stores

## Memory System Architecture

The memory system follows a layered architecture:

1. **Domain Layer**:
   - `MemoryItem`: Core domain model representing a memory item
   - `MemoryType`: Enumeration of memory item types
   - `MemoryStore` and `VectorStore` interfaces: Define the contract for memory adapters

2. **Application Layer**:
   - `MemoryManager`: Orchestrates operations across memory adapters
   - `SyncManager`: Manages synchronization between memory stores
   - `QueryRouter`: Routes queries to appropriate memory stores

3. **Adapters Layer**:
   - Concrete implementations of memory adapters for different storage backends

### Key Components

#### Memory Manager

The `MemoryManager` provides a unified interface to different memory adapters. It:

- Manages multiple memory adapters
- Routes operations to appropriate adapters
- Coordinates cross-store operations
- Handles embedding generation for vector search

#### Sync Manager

The `SyncManager` handles synchronization between different memory stores. It:

- Manages transactions across multiple stores
- Detects and resolves conflicts
- Provides rollback capabilities
- Queues updates for asynchronous processing

#### Query Router

The `QueryRouter` routes queries to appropriate memory stores. It:

- Analyzes queries to determine which stores to query
- Combines results from multiple stores
- Optimizes query execution

## Memory Adapters

DevSynth supports multiple memory adapters, each with its own strengths and limitations:

### TinyDB Memory Adapter

- **Storage**: JSON documents in a file or in-memory
- **Strengths**: Simple, lightweight, good for small datasets
- **Limitations**: No native transaction support, limited query capabilities
- **Best for**: Simple storage of structured data, configuration, and metadata

#### Serialization format

TinyDB and other document adapters serialize `MemoryItem` instances through the
`SerializedMemoryItem` typed dictionary.  Each record stores the enum value from
`MemoryType` (`memory_type.value`) alongside JSON-compatible metadata.  The
helpers coerce legacy records where the `memory_type` field contains the enum
name (for example, `"EXPAND_RESULTS"`) via `MemoryType.from_raw`, so old data
continues to load safely while new writes remain type checked.

### Graph Memory Adapter

- **Storage**: Graph database (NetworkX)
- **Strengths**: Relationship modeling, traversal queries
- **Limitations**: Performance with large graphs, no native transaction support
- **Best for**: Storing relationships between items, knowledge graphs

### Vector Store Adapters

- **Storage**: Vector databases (FAISS, ChromaDB)
- **Strengths**: Similarity search, embedding storage
- **Limitations**: Limited structured query support
- **Best for**: Semantic search, finding similar items

### Kuzu Memory Adapter

- **Storage**: Kuzu graph database
- **Strengths**: Persistent graph storage, better performance than NetworkX
- **Limitations**: More complex setup
- **Best for**: Production graph storage with performance requirements

### LMDB Memory Adapter

- **Storage**: Lightning Memory-Mapped Database
- **Strengths**: High performance, ACID transactions
- **Limitations**: More complex API
- **Best for**: High-performance storage with transaction requirements

### DuckDB Memory Adapter

- **Storage**: DuckDB analytical database
- **Strengths**: SQL queries, analytical capabilities
- **Limitations**: Not optimized for high-concurrency OLTP workloads
- **Best for**: Analytical queries over memory data

## Cross-Store Operations

Cross-store operations involve accessing or modifying data across multiple memory stores. These operations are complex because different stores have different capabilities and consistency models.

### Types of Cross-Store Operations

1. **Cross-Store Queries**: Querying data from multiple stores and combining the results
2. **Cross-Store Updates**: Updating related data in multiple stores
3. **Cross-Store Synchronization**: Keeping data consistent across multiple stores

### Challenges with Cross-Store Operations

1. **Atomicity**: Ensuring that operations across multiple stores are atomic
2. **Consistency**: Maintaining consistency across stores with different models
3. **Isolation**: Preventing interference between concurrent operations
4. **Durability**: Ensuring that changes are durable across all stores
5. **Error Handling**: Managing failures in one store without affecting others

## Transaction Support

Transaction support is critical for ensuring data integrity during cross-store operations. The current implementation has limitations that need to be addressed.

### Current Limitations

1. **Inconsistent Transaction Support**: Not all adapters support transactions natively
2. **Partial Failures**: Failures in one store can leave the system in an inconsistent state
3. **No Two-Phase Commit**: Lack of a proper two-phase commit protocol for cross-store transactions
4. **Limited Rollback**: Incomplete rollback capabilities for failed transactions

### Implementing Comprehensive Transaction Support

To address these limitations, we need to implement comprehensive transaction support across all memory adapters:

1. **Transaction Context**:
   ```python
   import uuid
   import time
   from typing import Dict, List, Any, Optional

   class MemoryRetrievalError(Exception):
       """Exception raised when memory retrieval fails."""
       pass

   class MemoryStorageError(Exception):
       """Exception raised when memory storage fails."""
       pass

   class CircuitBreakerOpenError(Exception):
       """Exception raised when circuit breaker is open."""
       pass

   class TransactionContext:
       def __init__(self, adapters):
           self.adapters = adapters
           self.transaction_id = str(uuid.uuid4())
           self.snapshots = {}
           self.operations = []

       def __enter__(self):
           # Begin transaction on all adapters
           for adapter in self.adapters:
               if hasattr(adapter, 'begin_transaction'):
                   adapter.begin_transaction(self.transaction_id)
               else:
                   # For adapters without native transaction support,
                   # take a snapshot of the current state
                   self.snapshots[adapter.id] = adapter.snapshot()
           return self

       def __exit__(self, exc_type, exc_val, exc_tb):
           if exc_type is None:
               # Commit transaction on all adapters
               self._commit()
           else:
               # Rollback transaction on all adapters
               self._rollback()

       def _commit(self):
           # Two-phase commit
           # Phase 1: Prepare
           prepared = []
           try:
               for adapter in self.adapters:
                   if hasattr(adapter, 'prepare_commit'):
                       adapter.prepare_commit(self.transaction_id)
                       prepared.append(adapter)
           except Exception as e:
               # If prepare fails, rollback prepared adapters
               for adapter in prepared:
                   adapter.rollback(self.transaction_id)
               raise e

           # Phase 2: Commit
           for adapter in self.adapters:
               if hasattr(adapter, 'commit'):
                   adapter.commit(self.transaction_id)

       def _rollback(self):
           # Rollback transaction on all adapters
           for adapter in self.adapters:
               if hasattr(adapter, 'rollback'):
                   adapter.rollback(self.transaction_id)
               else:
                   # For adapters without native transaction support,
                   # restore from snapshot
                   adapter.restore(self.snapshots.get(adapter.id))
   ```

2. **Adapter Transaction Support**:
   - Implement `begin_transaction`, `prepare_commit`, `commit`, and `rollback` methods for all adapters
   - For adapters without native transaction support, implement snapshot and restore capabilities

3. **Memory Manager Integration**:
   ```python
   # In memory_manager.py
   class MemoryManager:
       def __init__(self, adapters=None):
           self.adapters = adapters or {}

       def with_transaction(self, stores=None):
           """Context manager for transactions across multiple stores."""
           if stores is None:
               stores = list(self.adapters.keys())

           adapters = [self.adapters[store] for store in stores]
           return TransactionContext(adapters)

   # Usage example:
   from devsynth.domain.models.memory import MemoryItem, MemoryType

   # Initialize memory manager
   memory_manager = MemoryManager({
       'graph': GraphMemoryAdapter(),
       'tinydb': TinyDBMemoryAdapter()
   })

   # Create memory items
   graph_item = MemoryItem(id="graph_item_1", content="Graph content", memory_type=MemoryType.KNOWLEDGE_GRAPH)
   tinydb_item = MemoryItem(id="tinydb_item_1", content="TinyDB content", memory_type=MemoryType.DOCUMENTATION)

   # Use transaction context
   with memory_manager.with_transaction(['graph', 'tinydb']):
       memory_manager.adapters['graph'].store(graph_item)
       memory_manager.adapters['tinydb'].store(tinydb_item)
   ```

## Error Handling and Recovery

Robust error handling and recovery mechanisms are essential for maintaining data integrity during cross-store operations.

### Error Handling Strategies

1. **Try-Except-Finally Pattern**:
   ```python
   def cross_store_operation(self, stores):
       # Create snapshots for rollback
       snapshots = {store: self._create_snapshot(store) for store in stores}

       try:
           # Perform operations
           for store in stores:
               self._perform_operation(store)
       except Exception as e:
           # Rollback on error
           for store in stores:
               self._restore_snapshot(store, snapshots[store])
           raise e
       finally:
           # Clean up resources
           for store in stores:
               self._cleanup(store)
   ```

2. **Circuit Breaker Pattern**:
   ```python
   class CircuitBreaker:
       def __init__(self, failure_threshold=3, reset_timeout=60):
           self.failure_count = 0
           self.failure_threshold = failure_threshold
           self.reset_timeout = reset_timeout
           self.last_failure_time = 0
           self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN

       def execute(self, func, *args, **kwargs):
           if self.state == "OPEN":
               # Check if reset timeout has elapsed
               if time.time() - self.last_failure_time > self.reset_timeout:
                   self.state = "HALF-OPEN"
               else:
                   raise CircuitBreakerOpenError("Circuit breaker is open")

           try:
               result = func(*args, **kwargs)

               # Success, reset failure count
               if self.state == "HALF-OPEN":
                   self.state = "CLOSED"
                   self.failure_count = 0

               return result
           except Exception as e:
               # Failure, increment failure count
               self.failure_count += 1
               self.last_failure_time = time.time()

               if self.failure_count >= self.failure_threshold:
                   self.state = "OPEN"

               raise e
   ```

3. **Retry with Exponential Backoff**:
   ```python
   def retry_with_backoff(max_retries=3, initial_backoff=1, backoff_multiplier=2):
       def decorator(func):
           def wrapper(*args, **kwargs):
               retries = 0
               backoff = initial_backoff

               while retries < max_retries:
                   try:
                       return func(*args, **kwargs)
                   except Exception as e:
                       retries += 1
                       if retries >= max_retries:
                           raise e

                       # Wait with exponential backoff
                       time.sleep(backoff)
                       backoff *= backoff_multiplier
           return wrapper
       return decorator
   ```

### Recovery Mechanisms

1. **Snapshots and Rollbacks**:
   - Take snapshots of store state before operations
   - Restore from snapshots on failure

2. **Operation Logging**:
   - Log operations before execution
   - Use logs to replay operations after recovery

3. **Compensating Actions**:
   - Define compensating actions for each operation
   - Execute compensating actions on failure

## Fallback Mechanisms

Fallback mechanisms help maintain system availability when some memory stores are unavailable or experiencing issues.

### Store Prioritization

Define a priority order for memory stores and fall back to lower-priority stores when higher-priority stores are unavailable:

```python
def get_with_fallback(self, item_id, stores=None):
    """Get an item with fallback to other stores."""
    if stores is None:
        stores = self.store_priorities

    errors = {}

    for store in stores:
        try:
            item = self.adapters[store].retrieve(item_id)
            if item is not None:
                return item
        except Exception as e:
            errors[store] = str(e)
            continue

    # If we get here, all stores failed or returned None
    raise MemoryRetrievalError(f"Failed to retrieve item {item_id} from any store: {errors}")
```

### Read-Through and Write-Through Caching

Implement read-through and write-through caching to improve performance and provide fallback capabilities:

```python
def get_with_cache(self, item_id):
    """Get an item with read-through caching."""
    # Try to get from cache first
    item = self.cache.get(item_id)
    if item is not None:
        return item

    # Cache miss, try to get from primary store
    try:
        item = self.primary_store.retrieve(item_id)
        if item is not None:
            # Update cache
            self.cache.set(item_id, item)
            return item
    except Exception as e:
        # Primary store failed, log error
        self.logger.error(f"Primary store failed: {e}")

    # Try fallback stores
    for store in self.fallback_stores:
        try:
            item = store.retrieve(item_id)
            if item is not None:
                # Update cache
                self.cache.set(item_id, item)
                return item
        except Exception as e:
            # Fallback store failed, log error
            self.logger.error(f"Fallback store failed: {e}")

    # All stores failed
    return None
```

### Degraded Mode Operation

Define degraded mode operations that can continue with reduced functionality when some stores are unavailable:

```python
def store_with_degraded_mode(self, item):
    """Store an item with degraded mode support."""
    primary_success = False

    # Try to store in primary store
    try:
        self.primary_store.store(item)
        primary_success = True
    except Exception as e:
        # Primary store failed, log error
        self.logger.error(f"Primary store failed: {e}")

    # If primary store succeeded, try to store in secondary stores
    if primary_success:
        for store in self.secondary_stores:
            try:
                store.store(item)
            except Exception as e:
                # Secondary store failed, log error
                self.logger.error(f"Secondary store failed: {e}")
                # Continue with other secondary stores

    # If primary store failed, try to store in fallback store
    elif self.fallback_store is not None:
        try:
            self.fallback_store.store(item)
            # Set flag to indicate we're in degraded mode
            self.degraded_mode = True
            # Schedule reconciliation when primary store is available
            self.schedule_reconciliation()
        except Exception as e:
            # Fallback store failed, log error
            self.logger.error(f"Fallback store failed: {e}")
            # We're out of options, raise error
            raise MemoryStorageError("All stores failed")
```

## Testing Memory Integration

Comprehensive testing is essential for ensuring the reliability of memory integration. This section provides guidance on testing cross-store operations, transactions, error handling, and fallback mechanisms.

### Unit Testing

1. **Adapter Tests**:
   - Test each adapter in isolation
   - Verify CRUD operations
   - Test adapter-specific features

2. **Memory Manager Tests**:
   - Test routing to appropriate adapters
   - Test cross-store operations
   - Test transaction support

3. **Sync Manager Tests**:
   - Test synchronization between stores
   - Test conflict detection and resolution
   - Test transaction rollback

### Integration Testing

1. **Cross-Store Operation Tests**:
   - Test operations that span multiple stores
   - Verify data consistency across stores
   - Test with different combinations of stores

2. **Transaction Tests**:
   - Test transaction atomicity
   - Test transaction isolation
   - Test transaction durability

3. **Error Handling Tests**:
   - Test recovery from store failures
   - Test partial failures during cross-store operations
   - Test circuit breaker behavior

### Behavior Tests

1. **Scenario-Based Tests**:
   - Test real-world scenarios that involve multiple stores
   - Verify system behavior under different conditions
   - Test end-to-end workflows

2. **Failure Scenario Tests**:
   - Test system behavior under various failure scenarios
   - Verify recovery mechanisms
   - Test degraded mode operation

### Performance Testing

1. **Load Testing**:
   - Test system performance under load
   - Identify bottlenecks
   - Verify scalability

2. **Stress Testing**:
   - Test system behavior under extreme conditions
   - Verify stability under stress
   - Identify breaking points

## Best Practices

### Designing for Cross-Store Operations

1. **Minimize Cross-Store Dependencies**:
   - Design data models to minimize dependencies between stores
   - Use denormalization where appropriate to reduce cross-store queries

2. **Use Idempotent Operations**:
   - Design operations to be idempotent
   - This simplifies retry logic and error recovery

3. **Implement Eventual Consistency**:
   - Accept eventual consistency where appropriate
   - Use versioning to track changes and resolve conflicts

### Implementing Transactions

1. **Use Two-Phase Commit**:
   - Implement a two-phase commit protocol for cross-store transactions
   - Handle prepare, commit, and rollback phases properly

2. **Implement Compensating Actions**:
   - Define compensating actions for operations that can't be rolled back
   - Use these to restore consistency after failures

3. **Log Transaction Operations**:
   - Log operations before execution
   - Use logs for recovery and auditing

### Error Handling

1. **Implement Circuit Breakers**:
   - Use circuit breakers to prevent cascading failures
   - Implement fallback mechanisms for when circuit breakers are open

2. **Use Retry with Backoff**:
   - Implement retry logic with exponential backoff
   - Set appropriate retry limits and timeouts

3. **Provide Detailed Error Information**:
   - Log detailed error information
   - Include context to aid in debugging

### Testing

1. **Test Failure Scenarios**:
   - Test system behavior under various failure scenarios
   - Verify recovery mechanisms

2. **Use Chaos Engineering**:
   - Introduce random failures to test resilience
   - Verify system behavior under unexpected conditions

3. **Monitor Test Coverage**:
   - Track test coverage for memory integration code
   - Identify areas with insufficient coverage

## Troubleshooting

### Common Issues

1. **Inconsistent Data**:
   - **Symptoms**: Different stores return different values for the same item
   - **Causes**: Failed synchronization, race conditions, partial failures
   - **Solutions**: Implement robust transaction support, use versioning, improve error handling

2. **Transaction Failures**:
   - **Symptoms**: Operations fail with transaction-related errors
   - **Causes**: Partial failures, timeout issues, store-specific limitations
   - **Solutions**: Implement two-phase commit, improve rollback mechanisms, use compensating actions

3. **Performance Issues**:
   - **Symptoms**: Slow cross-store operations, high latency
   - **Causes**: Inefficient queries, lack of caching, store-specific performance issues
   - **Solutions**: Optimize queries, implement caching, use appropriate stores for different use cases

4. **Memory Leaks**:
   - **Symptoms**: Increasing memory usage over time
   - **Causes**: Unclosed resources, reference cycles, large cached objects
   - **Solutions**: Properly close resources, implement cache eviction, use weak references

### Debugging Techniques

1. **Enable Verbose Logging**:
   - Set log level to DEBUG for memory-related components
   - Log detailed information about operations and errors

2. **Use Transaction Tracing**:
   - Implement transaction tracing to track operations across stores
   - Analyze traces to identify issues

3. **Monitor Store State**:
   - Implement monitoring for store state
   - Track metrics like item count, operation latency, and error rate

4. **Inspect Store Contents**:
   - Implement tools to inspect store contents
   - Compare contents across stores to identify inconsistencies

## Reference

### Key Classes and Interfaces

- **MemoryItem**: Core domain model representing a memory item
- **MemoryType**: Enumeration of memory item types
- **MemoryStore**: Interface for memory adapters
- **VectorStore**: Interface for vector store adapters
- **MemoryManager**: Orchestrates operations across memory adapters
- **SyncManager**: Manages synchronization between memory stores
- **QueryRouter**: Routes queries to appropriate memory stores

### Memory Adapter Implementations

- **TinyDBMemoryAdapter**: Adapter for TinyDB
- **GraphMemoryAdapter**: Adapter for NetworkX graph database
- **FAISSVectorStore**: Adapter for FAISS vector database
- **ChromaDBVectorStore**: Adapter for ChromaDB vector database
- **KuzuMemoryAdapter**: Adapter for Kuzu graph database
- **LMDBMemoryAdapter**: Adapter for LMDB
- **DuckDBMemoryAdapter**: Adapter for DuckDB

### Related Documentation

- [Memory System Architecture](../architecture/memory_system.md)
- [Memory Adapter Development Guide](memory_adapter_development_guide.md)
- [Transaction Management Guide](transaction_management_guide.md)
- [Error Handling Best Practices](error_handling_best_practices.md)

---

_Last updated: August 1, 2025_
