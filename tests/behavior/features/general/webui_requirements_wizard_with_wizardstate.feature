Feature: WebUI Requirements Wizard with WizardState
  The requirements wizard should rely on WizardState to persist user input
  between steps, clamp navigation, and reset cleanly after completion.

  Scenario: Requirements wizard persists fields when navigating back
    Given the requirements wizard is ready
    When I enter "User Login" for the requirement title
    And I advance to the next requirements step
    And I enter "Allow users to log in" for the requirement description
    And I go back to the previous requirements step
    Then the wizard stores the title "User Login"
    And the wizard keeps the description "Allow users to log in" for step 2

  Scenario: Requirements wizard resets state after saving
    Given the requirements wizard is ready
    When I enter "User Login" for the requirement title
    And I advance to the next requirements step
    And I enter "Allow users to log in" for the requirement description
    And I advance to the next requirements step
    And I choose "functional" as the requirement type
    And I advance to the next requirements step
    And I choose "high" as the requirement priority
    And I advance to the next requirements step
    And I enter "Latency < 100ms" for the requirement constraints
    And I finish the requirements wizard
    Then the requirements wizard returns to step 1
    And the wizard clears the captured requirement data
    And the requirements summary is saved
