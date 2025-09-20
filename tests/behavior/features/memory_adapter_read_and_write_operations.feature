Feature: Memory adapter read and write operations
  As a DevSynth maintainer
  I want layered caches to expose symmetric read and write APIs
  So that adapters can rely on consistent semantics across components

  Background:
    Given a two-layer in-memory cache

  Scenario: write-through updates both layers
    When I write the key "task-001" with value "analyzed plan"
    Then each layer should store "analyzed plan" for "task-001"
    And reading "task-001" should return "analyzed plan"

  Scenario: missing keys raise errors
    When I attempt to read the key "unknown"
    Then a KeyError should be raised for "unknown"
