Feature: WebUI Specification Editor Extended
  As a developer
  I want to use all features of the specification editor in the WebUI
  So that I can efficiently manage and regenerate specifications

  Scenario: Load an existing specification file
    Given the WebUI is initialized
    And a specification file exists with content "existing spec"
    When I load the specification file
    Then the specification content should be displayed in the editor

  Scenario: Handle non-existent specification file
    Given the WebUI is initialized
    When I try to load a non-existent specification file
    Then the editor should show empty content

  Scenario: Edit and save without regenerating
    Given the WebUI is initialized
    And a specification file exists with content "original content"
    When I load the specification file
    And I edit the content to "updated content"
    And I save the specification without regenerating
    Then the specification file should be updated
    But the spec command should not be executed
