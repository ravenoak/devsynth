Feature: Release state check
  As a release maintainer
  I want verification to ensure published releases have tags
  So that release documentation matches repository state

  Scenario: Release verification fails without tag
    Given the release status is "published"
    When I verify the release state
    Then the release verification should fail

  Scenario: Release verification succeeds for draft release
    Given the release status is "draft"
    When I verify the release state
    Then the release verification should pass
