Feature: WebUI bridge message routing
  The WebUI router should surface sanitized messages for routed pages.

  @gui @medium
  Scenario: Routed page surfaces a sanitized success message
    Given the WebUI bridge is initialized
    And the stubbed sidebar selects "Bridge Success"
    When the "Bridge Success" page renders successfully
    Then the Streamlit stub records a sanitized success message

  @gui @medium
  Scenario: Routed page surfaces a sanitized error banner
    Given the WebUI bridge is initialized
    And the stubbed sidebar selects "Bridge Error"
    When the "Bridge Error" page raises an error
    Then the Streamlit stub records a sanitized error message
