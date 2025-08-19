Feature: Release state check
  As a release maintainer
  I want verification to ensure published releases have tags
  So that release documentation matches repository state

  Scenario: Release verification fails without tag
    When I verify the release state
    Then the release verification should fail
