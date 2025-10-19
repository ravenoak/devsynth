Feature: WebUI Serve Page
  As a developer
  I want to serve and manage applications in the WebUI
  So that I can easily deploy and test my applications

  Background:
    Given the WebUI is initialized

  Scenario: Navigate to Serve page
    When I navigate to "Serve"
    Then the Serve page should be displayed

  Scenario: Start serving an application
    When I navigate to "Serve"
    And I select an application to serve
    And I click the start button
    Then the application should start serving
    And the server status should show as running

  Scenario: Stop serving an application
    When I navigate to "Serve"
    And I select a running application
    And I click the stop button
    Then the application should stop serving
    And the server status should show as stopped

  Scenario: Configure server settings
    When I navigate to "Serve"
    And I select an application to serve
    And I click the settings button
    And I update the server settings
    And I save the settings
    Then the server settings should be updated
    And a success message should be displayed

  Scenario: View server logs
    When I navigate to "Serve"
    And I select a running application
    And I click the logs button
    Then the server logs should be displayed
    And the logs should update in real-time

  Scenario: Restart a running application
    When I navigate to "Serve"
    And I select a running application
    And I click the restart button
    Then the application should restart
    And the server status should show as running

  Scenario: View server metrics
    When I navigate to "Serve"
    And I select a running application
    And I click the metrics button
    Then the server metrics should be displayed
    And the metrics should update in real-time

  Scenario: Deploy application to production
    When I navigate to "Serve"
    And I select an application
    And I click the deploy to production button
    And I confirm the deployment
    Then the application should be deployed to production
    And a success message should be displayed
