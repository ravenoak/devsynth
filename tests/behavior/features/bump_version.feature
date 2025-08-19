Feature: Bump project version
  As a release engineer
  I want a helper script to bump the project version
  So that package metadata stays consistent

  Scenario: Update to next development version
    Given the project is tagged for release
    When I run the bump version script with "0.1.0-alpha.2.dev0"
    Then the project files reflect "0.1.0-alpha.2.dev0"
