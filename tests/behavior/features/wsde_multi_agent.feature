Feature: WSDE specialist rotation validates knowledge graph provenance
  The WSDE research cell coordinates dialectical reviews across the
  Research Lead, Critic, and Test Writer personas. The rotation should
  draw from the enhanced graph memory traversal API so each agent can
  reason about provenance and role metadata.

  Background:
    Given a graph memory adapter with research artefacts

  Scenario: Research Lead hands off to Critic and Test Writer
    When the specialist rotation runs from "node1"
    Then the research lead plan should include provenance entries
    And the critic result should approve the plan
    And the test writer should produce executable validation tests
