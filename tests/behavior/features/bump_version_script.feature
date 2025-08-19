Feature: Version bump script
  As a release maintainer
  I want a helper to bump the project version
  So that package metadata stays in sync

  Scenario: Bumping the version updates package metadata
    Given a sample __init__ file
    When I bump the version to "0.1.0-alpha.2.dev0"
    Then the __init__ version should be "0.1.0-alpha.2.dev0"
