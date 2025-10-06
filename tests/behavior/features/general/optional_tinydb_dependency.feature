Feature: Memory module handles missing TinyDB dependency
  In order to run DevSynth without TinyDB
  As a developer
  I want importing the memory module to succeed even when TinyDB is not installed

  Scenario: Importing memory module without TinyDB installed
    Given TinyDB is not installed
    When the memory module is imported
    Then the TinyDB adapter is unavailable
