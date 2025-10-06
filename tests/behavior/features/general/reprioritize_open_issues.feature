# Specification: docs/specifications/reprioritize-open-issues.md
Feature: Review and Reprioritize Open Issues
  As a maintainer
  I want to recalculate issue priorities from milestones
  So that the ticket tracker reflects the roadmap

  Background:
    Given an issue "issues/a.md" with milestone "Phase 1" and priority "low"
    And an issue "issues/b.md" with milestone "Phase 2" and priority "low"
    And an issue "issues/c.md" with milestone "Backlog" and priority "high"

  Scenario: Adjust priorities based on milestone
    When I run "devsynth reprioritize-issues"
    Then the issue "issues/a.md" should have priority "high"
    And the issue "issues/b.md" should have priority "medium"
    And the issue "issues/c.md" should have priority "low"

  Scenario Outline: Reprioritize various milestones
    Given an issue "<file>" with milestone "<milestone>" and priority "low"
    When I run "devsynth reprioritize-issues"
    Then the issue "<file>" should have priority "<expected>"

    Examples:
      | file            | milestone | expected |
      | issues/p1.md    | Phase 1   | high     |
      | issues/p2.md    | Phase 2   | medium   |
      | issues/back.md  | Backlog   | low      |
