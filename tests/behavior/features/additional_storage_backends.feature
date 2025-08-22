Feature: Additional Storage Backends
  The memory system selects a storage backend based on configuration.

  Scenario: S3 backend selected via environment variables
    Given the environment variable "DEVSYNTH_MEMORY_STORE" is "s3"
    And the environment variable "DEVSYNTH_S3_BUCKET" points to an existing bucket
    When the MemoryManager stores "data" as CODE memory
    Then the item can be retrieved with content "data"
