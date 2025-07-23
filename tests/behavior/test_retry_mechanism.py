"""BDD tests for the retry mechanism."""
import os
import pytest
from pytest_bdd import scenario
from .steps.test_retry_steps import *
feature_file = os.path.join(os.path.dirname(__file__), 'features', 'general',
    'retry_mechanism.feature')


@scenario(feature_file, 'Successful retry after transient errors')
def test_successful_retry_raises_error():
    """Test successful retry after transient errors.

ReqID: N/A"""
    pass


@scenario(feature_file, 'Failure after maximum retries')
def test_failure_after_max_retries_fails():
    """Test failure after maximum retries.

ReqID: N/A"""
    pass


@scenario(feature_file, 'Exponential backoff with jitter')
def test_exponential_backoff_with_jitter_succeeds():
    """Test exponential backoff with jitter.

ReqID: N/A"""
    pass
