---
author: ChatGPT
date: 2025-08-16
last_reviewed: 2025-08-16
status: draft
tags:
  - specification
title: Transactional consensus memory
version: 0.1.0a1
---

# Summary

## Socratic Checklist
- What is the problem?
- What proofs confirm the solution?

## Motivation

## What proofs confirm the solution?
- BDD scenarios in [`tests/behavior/features/consensus_transactional_memory.feature`](../../tests/behavior/features/consensus_transactional_memory.feature) ensure termination and expected outcomes.
- Finite state transitions and bounded loops guarantee termination.

Consensus decisions must be written consistently across core memory stores. Prior implementations stored team decisions in a single backend, risking divergence between LMDB, FAISS, and Kuzu layers.

## Specification
- Wrap consensus voting in a transaction spanning LMDB, FAISS, and Kuzu stores.
- Persist consensus decisions and summaries to all three stores.
- Store a vector representation of the decision in the FAISS index during the same transaction.

## Acceptance Criteria
- Consensus voting operates within a multi-store transaction including LMDB, FAISS, and Kuzu.
- Decision records and summaries appear in LMDB and Kuzu after consensus voting.
- A corresponding vector entry exists in FAISS for each consensus decision.
- Integration tests illustrate role reassignment where consensus data is shared across all stores.
