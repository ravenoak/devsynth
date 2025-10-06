# Related issue: ../../../../docs/specifications/consensus_transactional_memory.md
Feature: Role reassignment uses shared memory
  Reassigning roles and reaching consensus should commit decisions to all core stores.

  Scenario: reassigning roles persists consensus decision
    Given a collaborative WSDE team with LMDB, FAISS, and Kuzu stores
    When the team reassigns roles and reaches consensus on a task
    Then the consensus decision is persisted across LMDB, FAISS, and Kuzu
