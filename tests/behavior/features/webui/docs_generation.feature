Feature: WebUI Docs Generation Page
  As a developer
  I want to generate documentation for my project in the WebUI
  So that I can maintain up-to-date and comprehensive documentation

  Background:
    Given the WebUI is initialized

  Scenario: Navigate to Docs Generation page
    When I navigate to "Docs Generation"
    Then the docs generation page should be displayed

  Scenario: Generate project documentation
    When I navigate to "Docs Generation"
    And I submit the docs generation form
    Then the documentation should be generated
    And a success message should be displayed

  Scenario: Generate documentation with custom template
    When I navigate to "Docs Generation"
    And I select a custom documentation template
    And I submit the docs generation form
    Then the documentation should be generated with the custom template
    And a success message should be displayed

  Scenario: Generate documentation for specific components
    When I navigate to "Docs Generation"
    And I select specific components for documentation
    And I submit the docs generation form
    Then the documentation should be generated for the selected components
    And a success message should be displayed

  Scenario: Preview generated documentation
    When I navigate to "Docs Generation"
    And I submit the docs generation form
    And I click the preview button
    Then the generated documentation should be previewed

  Scenario: Export documentation in different formats
    When I navigate to "Docs Generation"
    And I select a documentation format
    And I submit the docs generation form
    And I click the export button
    Then the documentation should be exported in the selected format

  Scenario: View documentation generation history
    When I navigate to "Docs Generation"
    And I click the generation history button
    Then the documentation generation history should be displayed
    And previous generation results should be available for review
