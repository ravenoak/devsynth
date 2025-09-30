Feature: Autoresearch graph traversal and durability
  The enhanced graph adapter should preserve Autoresearch artefacts,
  bound traversal depth, and expose provenance digests.

  Background:
    Given a persistent enhanced graph memory adapter
    And a stored research artifact supporting "node2" derived from "node1"

  @fast
  Scenario: Traversal excludes research nodes by default
    When I traverse from "node1" to depth 2 excluding research artifacts
    Then the traversal result should equal "node2"
    When I traverse from "node1" to depth 2 including research artifacts
    Then the traversal result should contain the stored research artifact identifier

  @fast
  Scenario: Reload preserves research provenance hashes
    When I reload the enhanced graph memory adapter
    Then traversing from "node1" to depth 2 including research artifacts should contain the stored research artifact identifier
    And recomputing the stored research artifact hash should match the persisted digest
