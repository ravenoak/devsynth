"""
Integration tests for LM Studio provider with live server.

These tests verify the LM Studio provider works correctly with real server,
testing server availability probing and all functionality areas.
"""

import os
import time
from typing import Dict, List

import pytest
import httpx

from devsynth.application.llm.providers import LMStudioProvider
from devsynth.exceptions import DevSynthError


class TestLMStudioLiveIntegration:
    """Integration tests with live LM Studio server."""

    @pytest.fixture(scope="class")
    def lmstudio_available(self) -> bool:
        """Probe for LM Studio server availability."""
        try:
            response = httpx.get("http://localhost:1234/v1/models", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    @pytest.fixture
    def provider(self, lmstudio_available: bool) -> LMStudioProvider:
        """Create LM Studio provider for testing."""
        if not lmstudio_available:
            pytest.skip("LM Studio server not available")

        config = {"base_url": "http://localhost:1234/v1"}
        return LMStudioProvider(config)

    @pytest.mark.slow
    def test_server_availability_detection(self, lmstudio_available: bool):
        """Test detection of LM Studio server availability."""
        if not lmstudio_available:
            pytest.skip("LM Studio server not available")

        # If we get here, server should be available
        assert lmstudio_available is True

    @pytest.mark.slow
    def test_available_models_detection(self, provider: LMStudioProvider):
        """Test detection of available models on LM Studio server."""
        models = provider.list_available_models()

        # Should have at least one model available
        assert len(models) > 0, "No models detected on LM Studio server"

        # Each model should have required fields
        for model in models:
            assert "id" in model, f"Model missing 'id' field: {model}"
            assert "object" in model, f"Model missing 'object' field: {model}"
            assert model["object"] == "model", f"Invalid model object type: {model['object']}"

    @pytest.mark.slow
    def test_basic_generation_with_auto_model(self, provider: LMStudioProvider):
        """Test basic text generation with auto-selected model."""
        response = provider.generate("Hello, how are you today?")

        assert isinstance(response, str)
        assert len(response) > 0
        assert "error" not in response.lower()[:50]

        # Should be a reasonable response length
        assert len(response) < 10000  # Reasonable upper bound

    @pytest.mark.slow
    def test_basic_generation_with_specific_model(self, provider: LMStudioProvider):
        """Test basic text generation with specific model."""
        # Get available models
        models = provider.list_available_models()
        if len(models) == 0:
            pytest.skip("No models available for specific model testing")

        # Use first available model
        specific_model = models[0]["id"]

        # Test with specific model
        provider.model = specific_model
        response = provider.generate("What is the capital of France?")

        assert isinstance(response, str)
        assert len(response) > 0
        assert "paris" in response.lower() or "france" in response.lower()

    @pytest.mark.slow
    def test_context_generation_with_models(self, provider: LMStudioProvider):
        """Test context generation with available models."""
        models = provider.list_available_models()
        tested_models = []

        for model in models[:2]:  # Test first 2 models to avoid overwhelming server
            provider.model = model["id"]

            try:
                context = [
                    {"role": "system", "content": "You are a helpful coding assistant."},
                    {"role": "user", "content": "What is recursion in programming?"},
                ]

                response = provider.generate_with_context(
                    "Explain it in simple terms.",
                    context
                )

                assert isinstance(response, str)
                assert len(response) > 0
                # Should mention programming concepts
                assert any(term in response.lower() for term in ["function", "call", "itself", "recursive"])

                tested_models.append(model["id"])

            except DevSynthError as e:
                # Skip models that might not work for context generation
                if "context" in str(e).lower() or "model" in str(e).lower():
                    continue
                raise

        # Should have tested at least one model
        assert len(tested_models) > 0, "No models available for context testing"

    @pytest.mark.slow
    def test_parameter_variations(self, provider: LMStudioProvider):
        """Test generation with various parameter combinations."""
        models = provider.list_available_models()
        if len(models) == 0:
            pytest.skip("No models available for parameter testing")

        provider.model = models[0]["id"]

        # Test different temperatures
        for temp in [0.1, 0.5, 0.9, 1.5]:
            response = provider.generate(
                "Write a creative sentence.",
                parameters={"temperature": temp}
            )
            assert isinstance(response, str)
            assert len(response) > 0

        # Test different max_tokens
        for max_tokens in [50, 100, 200]:
            response = provider.generate(
                "Write a short story.",
                parameters={"max_tokens": max_tokens}
            )
            assert isinstance(response, str)
            assert len(response) > 0

    @pytest.mark.slow
    def test_performance_benchmarks(self, provider: LMStudioProvider):
        """Test performance characteristics of different models."""
        models = provider.list_available_models()

        performance_results = {}

        for model in models[:2]:  # Test first 2 models to avoid overwhelming server
            provider.model = model["id"]

            try:
                # Measure response time for multiple requests
                response_times = []
                for i in range(3):  # 3 requests per model
                    start_time = time.time()
                    response = provider.generate(f"Performance test request {i}")
                    end_time = time.time()

                    response_times.append(end_time - start_time)
                    assert isinstance(response, str)
                    assert len(response) > 0

                # Calculate average response time
                avg_response_time = sum(response_times) / len(response_times)
                performance_results[model["id"]] = {
                    "avg_response_time": avg_response_time,
                    "response_times": response_times,
                }

                # Basic performance assertions
                assert avg_response_time < 15.0, f"{model['id']} response time too slow: {avg_response_time}s"
                assert avg_response_time > 0.01, f"{model['id']} response time suspiciously fast: {avg_response_time}s"

            except DevSynthError as e:
                # Skip models that might not work for performance testing
                if "model" in str(e).lower() or "error" in str(e).lower():
                    continue
                raise

        # Should have tested at least one model
        assert len(performance_results) > 0, "No models available for performance testing"

        # Log performance results for analysis
        for model_id, results in performance_results.items():
            avg_time = results["avg_response_time"]
            print(f"{model_id}: Average response time = {avg_time:.2f}s")

    @pytest.mark.slow
    def test_token_tracking_integration(self, provider: LMStudioProvider):
        """Test token tracking with real server responses."""
        models = provider.list_available_models()
        if len(models) == 0:
            pytest.skip("No models available for token tracking test")

        provider.model = models[0]["id"]

        # Test with a moderately long prompt
        long_prompt = "Explain quantum computing in detail. " * 10

        response = provider.generate(long_prompt)

        assert isinstance(response, str)
        assert len(response) > 0

        # Verify token tracker is working (basic check)
        assert hasattr(provider, 'token_tracker')
        assert provider.token_tracker is not None

    @pytest.mark.slow
    def test_error_handling_with_real_server(self, provider: LMStudioProvider):
        """Test error handling with real server responses."""
        models = provider.list_available_models()
        if len(models) == 0:
            pytest.skip("No models available for error handling test")

        # Test with invalid model (should fail)
        provider.model = "invalid-model-name"

        with pytest.raises(DevSynthError) as exc_info:
            provider.generate("Hello")

        assert "LM Studio API error" in str(exc_info.value)

    @pytest.mark.slow
    def test_model_switching_performance(self, provider: LMStudioProvider):
        """Test performance when switching between models."""
        models = provider.list_available_models()
        if len(models) < 2:
            pytest.skip("Need at least 2 models for switching test")

        switch_times = []

        for i, model in enumerate(models[:2]):  # Test first 2 models
            # Time the model switch and first request
            start_time = time.time()

            provider.model = model["id"]
            response = provider.generate("Model switching test")

            end_time = time.time()
            switch_times.append(end_time - start_time)

            assert isinstance(response, str)
            assert len(response) > 0

        # Model switching should be reasonably fast
        for i, switch_time in enumerate(switch_times):
            assert switch_time < 5.0, f"Model switch {i} took too long: {switch_time}s"

    @pytest.mark.slow
    def test_concurrent_requests_handling(self, provider: LMStudioProvider):
        """Test handling of concurrent requests."""
        import threading

        models = provider.list_available_models()
        if len(models) == 0:
            pytest.skip("No models available for concurrent test")

        provider.model = models[0]["id"]

        results = []
        errors = []

        def make_request(request_id: int):
            try:
                response = provider.generate(f"Concurrent request {request_id}")
                results.append((request_id, response))
            except Exception as e:
                errors.append((request_id, e))

        # Start multiple concurrent requests
        threads = []
        for i in range(3):  # 3 concurrent requests
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Should have some successful responses
        assert len(results) > 0, "No successful responses in concurrent test"
        assert len(errors) < len(threads), "Too many errors in concurrent test"

        # All successful responses should be strings
        for request_id, response in results:
            assert isinstance(response, str)
            assert len(response) > 0

    @pytest.mark.slow
    def test_long_context_handling(self, provider: LMStudioProvider):
        """Test handling of longer conversation contexts."""
        models = provider.list_available_models()
        if len(models) == 0:
            pytest.skip("No models available for context test")

        provider.model = models[0]["id"]

        # Create a conversation with multiple exchanges
        context = [
            {"role": "system", "content": "You are a helpful assistant."},
        ]

        # Add several conversation turns
        for i in range(3):
            context.append({"role": "user", "content": f"Question {i} about AI"})
            context.append({"role": "assistant", "content": f"Answer {i} about AI"})

        # Add a final question
        final_response = provider.generate_with_context("What is the future of AI?", context)

        assert isinstance(final_response, str)
        assert len(final_response) > 0

    @pytest.mark.slow
    def test_response_quality_assessment(self, provider: LMStudioProvider):
        """Test response quality across different models."""
        models = provider.list_available_models()
        if len(models) == 0:
            pytest.skip("No models available for quality testing")

        quality_scores = {}

        for model in models[:2]:  # Test first 2 models
            provider.model = model["id"]

            try:
                response = provider.generate("Explain machine learning in simple terms.")

                # Basic quality metrics
                quality_score = 0

                # Length check (should be substantial but not excessive)
                if 20 < len(response) < 2000:
                    quality_score += 1

                # Relevance check (should contain relevant terms)
                response_lower = response.lower()
                if any(term in response_lower for term in ["machine", "learning", "ai", "algorithm"]):
                    quality_score += 1

                # Coherence check (shouldn't contain obvious errors)
                if "error" not in response_lower[:100]:
                    quality_score += 1

                quality_scores[model["id"]] = quality_score

            except DevSynthError as e:
                # Skip models that might not work for quality testing
                if "model" in str(e).lower() or "error" in str(e).lower():
                    continue
                raise

        # Should have tested at least one model
        tested_models = [model_id for model_id in quality_scores.keys() if quality_scores[model_id] > 0]
        assert len(tested_models) > 0, "No models available for quality testing"

        # All tested models should achieve reasonable quality scores
        for model_id, score in quality_scores.items():
            if score > 0:  # Only check models that were actually tested
                assert score >= 2, f"{model_id} quality score too low: {score}/3"


class TestLMStudioIntegrationEdgeCases:
    """Test edge cases with live LM Studio server."""

    @pytest.fixture(scope="class")
    def lmstudio_available(self) -> bool:
        """Probe for LM Studio server availability."""
        try:
            response = httpx.get("http://localhost:1234/v1/models", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    @pytest.mark.slow
    def test_very_long_prompt_handling(self, lmstudio_available: bool):
        """Test handling of very long prompts."""
        if not lmstudio_available:
            pytest.skip("LM Studio server not available")

        config = {"base_url": "http://localhost:1234/v1"}
        provider = LMStudioProvider(config)

        models = provider.list_available_models()
        if len(models) == 0:
            pytest.skip("No models available for long prompt test")

        provider.model = models[0]["id"]

        # Create a long prompt that approaches context limits
        long_prompt = "Explain quantum computing in detail. " * 50

        try:
            response = provider.generate(long_prompt)
            assert isinstance(response, str)
            assert len(response) > 0
        except DevSynthError as e:
            # Long prompts might be rejected - this is acceptable
            assert "token" in str(e).lower() or "limit" in str(e).lower()

    @pytest.mark.slow
    def test_unicode_and_special_characters(self, lmstudio_available: bool):
        """Test handling of Unicode and special characters."""
        if not lmstudio_available:
            pytest.skip("LM Studio server not available")

        config = {"base_url": "http://localhost:1234/v1"}
        provider = LMStudioProvider(config)

        models = provider.list_available_models()
        if len(models) == 0:
            pytest.skip("No models available for Unicode test")

        provider.model = models[0]["id"]

        unicode_prompt = "Say hello in these languages: English, Chinese (你好), Spanish (¡Hola!), and include emoji 🌟"

        response = provider.generate(unicode_prompt)

        assert isinstance(response, str)
        assert len(response) > 0

        # Check for Unicode content in response
        # This is a basic check - real tests would be more sophisticated
        assert len(response) > 10  # Should contain substantial response

    @pytest.mark.slow
    def test_empty_and_whitespace_prompts(self, lmstudio_available: bool):
        """Test handling of empty and whitespace-only prompts."""
        if not lmstudio_available:
            pytest.skip("LM Studio server not available")

        config = {"base_url": "http://localhost:1234/v1"}
        provider = LMStudioProvider(config)

        models = provider.list_available_models()
        if len(models) == 0:
            pytest.skip("No models available for empty prompt test")

        provider.model = models[0]["id"]

        # Test empty prompt
        with pytest.raises(DevSynthError):
            provider.generate("")

        # Test whitespace-only prompt
        with pytest.raises(DevSynthError):
            provider.generate("   ")

    @pytest.mark.slow
    def test_server_timeout_handling(self, lmstudio_available: bool):
        """Test handling of server timeouts."""
        if not lmstudio_available:
            pytest.skip("LM Studio server not available")

        # Test with very short timeout
        config = {
            "base_url": "http://localhost:1234/v1",
            "timeout": 0.001  # Very short timeout
        }
        provider = LMStudioProvider(config)

        models = provider.list_available_models()
        if len(models) == 0:
            pytest.skip("No models available for timeout test")

        provider.model = models[0]["id"]

        # This should timeout or fail gracefully
        with pytest.raises(DevSynthError):
            provider.generate("Timeout test")


class TestLMStudioIntegrationPerformance:
    """Test performance characteristics of LM Studio integration."""

    @pytest.fixture(scope="class")
    def lmstudio_available(self) -> bool:
        """Probe for LM Studio server availability."""
        try:
            response = httpx.get("http://localhost:1234/v1/models", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    @pytest.mark.slow
    def test_latency_benchmarks_across_models(self, lmstudio_available: bool):
        """Benchmark latency across different models."""
        if not lmstudio_available:
            pytest.skip("LM Studio server not available")

        config = {"base_url": "http://localhost:1234/v1"}
        provider = LMStudioProvider(config)

        models = provider.list_available_models()

        latency_results = []

        for model in models[:2]:  # Test first 2 models
            provider.model = model["id"]

            try:
                # Measure latency for multiple requests
                latencies = []
                for i in range(3):  # 3 requests per model
                    start_time = time.time()
                    response = provider.generate(f"Latency test {i}")
                    end_time = time.time()

                    latency = end_time - start_time
                    latencies.append(latency)

                    assert isinstance(response, str)
                    assert len(response) > 0

                # Calculate statistics
                avg_latency = sum(latencies) / len(latencies)
                max_latency = max(latencies)
                min_latency = min(latencies)

                latency_results.append({
                    "model": model["id"],
                    "avg": avg_latency,
                    "max": max_latency,
                    "min": min_latency,
                    "samples": latencies,
                })

            except DevSynthError as e:
                # Skip models that might not work for latency testing
                if "model" in str(e).lower() or "error" in str(e).lower():
                    continue
                raise

        # Should have tested at least one model
        assert len(latency_results) > 0, "No models available for latency testing"

        # Log results for analysis
        for results in latency_results:
            print(f"{results['model']} latency: avg={results['avg']:.2f}s, "
                  f"min={results['min']:.2f}s, max={results['max']:.2f}s")

        # Performance assertions
        for results in latency_results:
            # Average should be reasonable (< 10s for local models)
            assert results["avg"] < 10.0, f"{results['model']} average latency too high: {results['avg']}s"

            # Maximum should be acceptable (< 20s)
            assert results["max"] < 20.0, f"{results['model']} max latency too high: {results['max']}s"

            # Should have reasonable consistency
            assert results["max"] < results["avg"] * 3, f"{results['model']} latency too variable"

    @pytest.mark.slow
    def test_throughput_measurement(self, lmstudio_available: bool):
        """Test throughput capabilities."""
        if not lmstudio_available:
            pytest.skip("LM Studio server not available")

        config = {"base_url": "http://localhost:1234/v1"}
        provider = LMStudioProvider(config)

        models = provider.list_available_models()
        if len(models) == 0:
            pytest.skip("No models available for throughput test")

        provider.model = models[0]["id"]

        # Measure requests per second
        start_time = time.time()
        request_count = 0

        # Make requests for 10 seconds
        while time.time() - start_time < 10.0:
            try:
                response = provider.generate(f"Throughput test {request_count}")
                assert isinstance(response, str)
                assert len(response) > 0
                request_count += 1
            except DevSynthError as e:
                # If we hit rate limits or other errors, stop the test
                if "rate limit" in str(e).lower() or "error" in str(e).lower():
                    break
                else:
                    raise

        elapsed = time.time() - start_time
        requests_per_second = request_count / elapsed if elapsed > 0 else 0

        print(f"Throughput: {requests_per_second:.2f} requests/second ({request_count} requests in {elapsed:.2f}s)")

        # Should achieve reasonable throughput (> 1 request per 10 seconds)
        assert request_count > 0, "No requests completed"
        assert requests_per_second > 0.1, f"Throughput too low: {requests_per_second} req/s"
