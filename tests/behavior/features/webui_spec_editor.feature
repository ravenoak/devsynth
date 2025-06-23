Feature: WebUI Specification Editor
  As a developer
  I want to edit specification files in the WebUI
  So that I can regenerate specifications after making changes

  Scenario: Edit and regenerate a specification file
    Given the WebUI is initialized
    When I edit a specification file
    Then the spec command should be executed
    And the specification should be displayed
