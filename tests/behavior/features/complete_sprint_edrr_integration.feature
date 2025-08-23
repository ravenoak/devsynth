# Specification: docs/specifications/complete-sprint-edrr-integration.md
Feature: Complete Sprint-EDRR integration
  As a sprint facilitator
  I want to translate sprint ceremonies into EDRR phases
  So that DevSynth can align Agile data with EDRR cycles

  Background:
    Given a sprint adapter with default ceremony mappings

  Scenario: Align sprint planning with EDRR phases
    Given sprint planning sections for planning and review
    When the sections are aligned to EDRR phases
    Then planning data maps to the Expand phase
    And review data maps to the Refine phase

  Scenario: Align sprint review feedback with EDRR phases
    Given sprint review outcomes for the review ceremony
    When the feedback is aligned to EDRR phases
    Then the Refine phase contains the review feedback
    And unrelated ceremonies are ignored
