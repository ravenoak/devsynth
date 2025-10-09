"""Unit tests for the enhanced Agent API implementation."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from devsynth.interface.agentapi_enhanced import (
    RateLimiterState,
    health_endpoint,
    metrics_endpoint,
    router,
)
from devsynth.interface.agentapi_models import (
    CodeRequest,
    DoctorRequest,
    EDRRCycleRequest,
    GatherRequest,
    InitRequest,
    SpecRequest,
    SynthesisTarget,
    SynthesizeRequest,
)


class TestRateLimiter:
    """Test the rate limiting functionality."""

    @pytest.mark.fast
    def test_rate_limiter_initialization(self):
        """Test that RateLimiterState initializes correctly."""
        limiter = RateLimiterState()

        assert limiter.buckets == {}
        assert limiter.window_seconds == 60
        assert limiter.limit == 10

    @pytest.mark.fast
    def test_rate_limiter_record_request(self):
        """Test recording requests in the rate limiter."""
        limiter = RateLimiterState()
        client_ip = "127.0.0.1"
        timestamp = 1000.0

        # Record a request
        limiter.record(client_ip, timestamp=timestamp)

        # Should have recorded the request
        assert client_ip in limiter.buckets
        assert len(limiter.buckets[client_ip]) == 1
        assert limiter.buckets[client_ip][0] == timestamp

    @pytest.mark.fast
    def test_rate_limiter_count_within_limit(self):
        """Test that requests within limit are counted correctly."""
        limiter = RateLimiterState()
        client_ip = "127.0.0.1"

        # Record requests within limit
        limiter.record(client_ip, timestamp=1000.0)
        limiter.record(client_ip, timestamp=1001.0)

        # Should count correctly
        assert limiter.count(client_ip) == 2

    @pytest.mark.fast
    def test_rate_limiter_count_exceeds_limit(self):
        """Test that requests exceeding limit are counted correctly."""
        limiter = RateLimiterState()
        client_ip = "127.0.0.1"

        # Record requests exceeding limit
        for i in range(15):  # Exceeds default limit of 10
            limiter.record(client_ip, timestamp=1000.0 + i)

        # Should count correctly
        assert limiter.count(client_ip) == 15

    @pytest.mark.fast
    def test_rate_limiter_prune_old_requests(self):
        """Test that old requests are pruned."""
        limiter = RateLimiterState()
        client_ip = "127.0.0.1"

        # Record old and new requests
        limiter.record(client_ip, timestamp=0)  # Old timestamp
        limiter.record(client_ip, timestamp=1000)  # Recent timestamp

        # Prune old requests (window is 60 seconds, current time is 1000)
        limiter.prune(client_ip, now=1000, window=60)

        # Should have only the recent request
        assert len(limiter.buckets[client_ip]) == 1
        assert limiter.buckets[client_ip][0] == 1000

    @pytest.mark.fast
    def test_rate_limiter_multiple_clients(self):
        """Test rate limiting with multiple clients."""
        limiter = RateLimiterState()

        # Record requests from different clients
        limiter.record("127.0.0.1", timestamp=1000.0)
        limiter.record("127.0.0.2", timestamp=1000.0)

        # Each client should have their own bucket
        assert limiter.count("127.0.0.1") == 1
        assert limiter.count("127.0.0.2") == 1
        assert limiter.count("127.0.0.3") == 0  # New client


class TestAPIEndpoints:
    """Test API endpoints."""

    @pytest.mark.fast
    def test_health_endpoint_exists(self):
        """Test that health endpoint function exists."""
        from devsynth.interface.agentapi_enhanced import health_endpoint

        assert callable(health_endpoint)

    @pytest.mark.fast
    def test_metrics_endpoint_exists(self):
        """Test that metrics endpoint function exists."""
        from devsynth.interface.agentapi_enhanced import metrics_endpoint

        assert callable(metrics_endpoint)

    @pytest.mark.fast
    def test_init_request_model(self):
        """Test the init request model."""
        init_request = InitRequest(
            path=".", project_root=None, language="python", goals="test goals"
        )

        assert init_request.path == "."
        assert init_request.language == "python"
        assert init_request.goals == "test goals"

    @pytest.mark.fast
    def test_gather_request_model(self):
        """Test the gather request model."""
        gather_request = GatherRequest(
            goals="test goals", constraints="test constraints"
        )

        assert gather_request.goals == "test goals"
        assert gather_request.constraints == "test constraints"

    @pytest.mark.fast
    def test_synthesize_request_model(self):
        """Test the synthesize request model."""
        synthesize_request = SynthesizeRequest(target=SynthesisTarget.UNIT)

        assert synthesize_request.target == SynthesisTarget.UNIT

    @pytest.mark.fast
    def test_spec_request_model(self):
        """Test the spec request model."""
        spec_request = SpecRequest(requirements_file="requirements.md")

        assert spec_request.requirements_file == "requirements.md"

    @pytest.mark.fast
    def test_code_request_model(self):
        """Test the code request model."""
        code_request = CodeRequest(output_dir=".")

        assert code_request.output_dir == "."

    @pytest.mark.fast
    def test_doctor_request_model(self):
        """Test the doctor request model."""
        doctor_request = DoctorRequest(path=".", fix=False)

        assert doctor_request.path == "."
        assert doctor_request.fix is False

    @pytest.mark.fast
    def test_edrr_cycle_request_model(self):
        """Test the EDRR cycle request model."""
        edrr_request = EDRRCycleRequest(prompt="test prompt", max_iterations=5)

        assert edrr_request.prompt == "test prompt"
        assert edrr_request.max_iterations == 5


class TestRouter:
    """Test FastAPI router functionality."""

    @pytest.mark.fast
    def test_router_exists(self):
        """Test that router is defined."""
        assert router is not None
        assert hasattr(router, "routes")


class TestRateLimitingIntegration:
    """Test rate limiting integration functionality."""

    @pytest.mark.fast
    def test_rate_limiting_logic_integration(self):
        """Test the rate limiting logic integration."""
        # Test the core logic without full FastAPI setup
        limiter = RateLimiterState()

        # Record a request
        limiter.record("127.0.0.1", timestamp=1000.0)

        # Check that it was recorded
        assert limiter.count("127.0.0.1") == 1


class TestErrorHandling:
    """Test error handling in the enhanced API."""

    @pytest.mark.fast
    def test_error_response_structure(self):
        """Test error response structure."""
        from devsynth.interface.agentapi_enhanced import ErrorResponse

        error_response = ErrorResponse(error="Test error", details="Test details")

        assert error_response.error == "Test error"
        assert error_response.details == "Test details"


class TestEndpointIntegration:
    """Test endpoint integration and response models."""

    @pytest.mark.medium
    def test_response_models_can_be_instantiated(self):
        """Test that response models can be instantiated."""
        from devsynth.interface.agentapi_enhanced import WorkflowResponse

        # Test that response models can be instantiated
        response = WorkflowResponse(messages=("Test message",), metadata=None)

        assert len(response.messages) == 1
        assert response.messages[0] == "Test message"
        assert response.metadata is None

    @pytest.mark.fast
    def test_request_models_validation(self):
        """Test that request models have proper validation."""
        # Test that request models validate correctly
        init_request = InitRequest(
            path=".", project_root=None, language="python", goals="test goals"
        )

        assert init_request.path == "."
        assert init_request.language == "python"
        assert init_request.goals == "test goals"
