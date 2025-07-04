
Feature: Spec Command
  As a developer
  I want to generate specifications from requirements
  So that I can create a structured development plan

  Scenario: Generate specifications from requirements file
    When I run the command "devsynth spec --requirements-file requirements.md"
    Then the spec command should process "requirements.md"
