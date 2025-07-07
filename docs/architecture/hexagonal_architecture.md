---
author: DevSynth Team
date: '2025-05-30'
last_reviewed: '2025-05-30'
status: published
tags:

- architecture
- hexagonal
- ports-and-adapters
- design

title: Hexagonal Architecture Guide
version: 1.0.0
---

# Hexagonal Architecture Guide

This document explains the hexagonal (Hexagonal Architecture) architecture used in DevSynth.

## Overview

DevSynth uses a hexagonal architecture to separate core business logic from external systems. This improves testability, maintainability, and flexibility.

## Layers

- **Domain Layer**: Core business logic and models
- **Application Layer**: Use cases and orchestration
- **Ports Layer**: Interfaces for adapters
- **Adapters Layer**: Integrations with external systems (CLI, APIs, databases)


## Benefits

- Decouples business logic from infrastructure
- Makes it easy to add or replace adapters
- Facilitates automated testing


See [Architecture Overview](overview.md) and [Agent System](agent_system.md) for more details.