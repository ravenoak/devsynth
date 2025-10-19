"""
Integration tests for OpenRouter provider with live API.

These tests verify the OpenRouter provider works correctly with real API calls,
testing multiple free-tier models and all functionality areas.
"""

import os
import time
from typing import Dict, List

import pytest

from devsynth.application.llm.openrouter_provider import (
    OpenRouterConnectionError,
    OpenRouterModelError,
    OpenRouterProvider,
)

# Skip all tests if OpenRouter API key is not available
pytestmark = [
    pytest.mark.requires_resource("openrouter"),
    pytest.mark.integration,
]


class TestOpenRouterLiveIntegration:
    """Integration tests with live OpenRouter API."""

    @pytest.fixture(scope="class")
    def api_key(self) -> str:
        """Get OpenRouter API key from environment."""
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            pytest.skip("OPENROUTER_API_KEY environment variable not set")
        return api_key

    @pytest.fixture
    def provider(self, api_key: str) -> OpenRouterProvider:
        """Create OpenRouter provider for testing."""
        config = {"openrouter_api_key": api_key}
        return OpenRouterProvider(config)

    @pytest.mark.slow
    def test_basic_generation_gemini_flash(self, provider: OpenRouterProvider):
        """Test basic text generation with Gemini Flash (free tier)."""
        # Configure for Gemini Flash
        provider.model = "google/gemini-flash-1.5"

        response = provider.generate("Hello, how are you today?")

        assert isinstance(response, str)
        assert len(response) > 0
        assert "error" not in response.lower()[:50]

        # Should be a reasonable response length
        assert len(response) < 10000  # Reasonable upper bound

    @pytest.mark.slow
    def test_basic_generation_llama_8b(self, provider: OpenRouterProvider):
        """Test basic text generation with Llama 3.1 8B (free tier)."""
        # Configure for Llama 3.1 8B
        provider.model = "meta-llama/llama-3.1-8b-instruct"

        response = provider.generate("What is the capital of France?")

        assert isinstance(response, str)
        assert len(response) > 0
        assert "paris" in response.lower() or "france" in response.lower()

    @pytest.mark.slow
    def test_basic_generation_mistral_7b(self, provider: OpenRouterProvider):
        """Test basic text generation with Mistral 7B (free tier)."""
        # Configure for Mistral 7B
        provider.model = "mistralai/mistral-7b-instruct"

        response = provider.generate("Write a short haiku about programming.")

        assert isinstance(response, str)
        assert len(response) > 0
        # Haiku should be relatively short
        assert len(response) < 500

    @pytest.mark.slow
    def test_context_generation_with_all_models(self, provider: OpenRouterProvider):
        """Test context generation with all free-tier models."""
        free_tier_models = [
            "google/gemini-flash-1.5",
            "meta-llama/llama-3.1-8b-instruct",
            "mistralai/mistral-7b-instruct",
        ]

        context = [
            {"role": "system", "content": "You are a helpful coding assistant."},
            {"role": "user", "content": "What is recursion in programming?"},
        ]

        for model in free_tier_models:
            provider.model = model

            response = provider.generate_with_context(
                "Explain it in simple terms.", context
            )

            assert isinstance(response, str)
            assert len(response) > 0
            # Should mention programming concepts
            assert any(
                term in response.lower()
                for term in ["function", "call", "itself", "recursive"]
            )

    @pytest.mark.slow
    def test_embedding_generation(self, provider: OpenRouterProvider):
        """Test embedding generation with OpenRouter."""
        # Use OpenAI-compatible embedding model
        provider.model = "text-embedding-ada-002"

        text = "The quick brown fox jumps over the lazy dog"
        embedding = provider.get_embedding(text)

        assert isinstance(embedding, list)
        assert len(embedding) > 100  # Reasonable embedding dimension
        assert all(isinstance(x, (int, float)) for x in embedding)

        # Test multiple texts
        texts = ["Hello world", "Machine learning is fascinating"]
        embeddings = provider.get_embedding(texts)

        assert len(embeddings) == 2
        assert len(embeddings[0]) == len(embeddings[1])  # Same dimensions

    @pytest.mark.slow
    def test_parameter_variations(self, provider: OpenRouterProvider):
        """Test generation with various parameter combinations."""
        provider.model = "google/gemini-flash-1.5"

        # Test different temperatures
        for temp in [0.1, 0.5, 0.9, 1.5]:
            response = provider.generate(
                "Write a creative sentence.", parameters={"temperature": temp}
            )
            assert isinstance(response, str)
            assert len(response) > 0

        # Test different max_tokens
        for max_tokens in [50, 100, 200]:
            response = provider.generate(
                "Write a short story.", parameters={"max_tokens": max_tokens}
            )
            assert isinstance(response, str)
            assert len(response) > 0

    @pytest.mark.slow
    def test_performance_benchmarks(self, provider: OpenRouterProvider):
        """Test performance characteristics of different models."""
        models_to_test = [
            "google/gemini-flash-1.5",
            "meta-llama/llama-3.1-8b-instruct",
            "mistralai/mistral-7b-instruct",
        ]

        performance_results = {}

        for model in models_to_test:
            provider.model = model

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
            performance_results[model] = {
                "avg_response_time": avg_response_time,
                "response_times": response_times,
            }

        # Log performance results for analysis
        for model, results in performance_results.items():
            avg_time = results["avg_response_time"]
            print(f"{model}: Average response time = {avg_time:.2f}s")

            # Basic performance assertions
            assert avg_time < 10.0, f"{model} response time too slow: {avg_time}s"
            assert (
                avg_time > 0.1
            ), f"{model} response time suspiciously fast: {avg_time}s"

    @pytest.mark.slow
    def test_token_tracking_integration(self, provider: OpenRouterProvider):
        """Test token tracking with real API responses."""
        provider.model = "google/gemini-flash-1.5"

        # Test with a moderately long prompt
        long_prompt = "Explain quantum computing in detail. " * 10

        response = provider.generate(long_prompt)

        assert isinstance(response, str)
        assert len(response) > 0

        # Verify token tracker is working (basic check)
        assert hasattr(provider, "token_tracker")
        assert provider.token_tracker is not None

    @pytest.mark.slow
    def test_error_handling_with_real_api(self, api_key: str):
        """Test error handling with real API responses."""
        # Test with invalid API key (should fail authentication)
        config = {"openrouter_api_key": "invalid-key-for-testing"}
        provider = OpenRouterProvider(config)

        with pytest.raises(OpenRouterConnectionError) as exc_info:
            provider.generate("Hello")

        assert "OpenRouter API error" in str(exc_info.value)

    @pytest.mark.slow
    def test_rate_limiting_behavior(self, provider: OpenRouterProvider):
        """Test rate limiting behavior with free-tier models."""
        provider.model = "google/gemini-flash-1.5"

        # Make multiple rapid requests to potentially trigger rate limits
        responses = []
        start_time = time.time()

        for i in range(5):  # Make 5 rapid requests
            try:
                response = provider.generate(f"Rate limit test {i}")
                responses.append(response)
            except OpenRouterConnectionError as e:
                if "rate limit" in str(e).lower():
                    # If we hit rate limits, that's expected behavior
                    print(f"Rate limit hit on request {i}: {e}")
                    break
                else:
                    raise  # Re-raise if it's not a rate limit error

        end_time = time.time()
        duration = end_time - start_time

        # Should complete in reasonable time (even if rate limited)
        assert duration < 60.0, f"Rate limit test took too long: {duration}s"

        # Should have gotten at least some responses
        assert len(responses) > 0, "No responses received"

    @pytest.mark.slow
    def test_model_switching_performance(self, provider: OpenRouterProvider):
        """Test performance when switching between models."""
        models = [
            "google/gemini-flash-1.5",
            "meta-llama/llama-3.1-8b-instruct",
            "mistralai/mistral-7b-instruct",
        ]

        switch_times = []

        for model in models:
            # Time the model switch and first request
            start_time = time.time()

            provider.model = model
            response = provider.generate("Model switching test")

            end_time = time.time()
            switch_times.append(end_time - start_time)

            assert isinstance(response, str)
            assert len(response) > 0

        # Model switching should be reasonably fast
        for i, switch_time in enumerate(switch_times):
            assert switch_time < 5.0, f"Model switch {i} took too long: {switch_time}s"

    @pytest.mark.slow
    def test_concurrent_requests_handling(self, provider: OpenRouterProvider):
        """Test handling of concurrent requests."""
        import threading

        provider.model = "google/gemini-flash-1.5"

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
    def test_provider_availability_check(self, api_key: str):
        """Test that provider correctly reports availability."""
        config = {"openrouter_api_key": api_key}

        # Provider should initialize successfully with valid API key
        provider = OpenRouterProvider(config)

        # Basic functionality should work
        response = provider.generate("Availability test")
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.slow
    def test_long_context_handling(self, provider: OpenRouterProvider):
        """Test handling of longer conversation contexts."""
        provider.model = "google/gemini-flash-1.5"  # Good context window

        # Create a conversation with multiple exchanges
        context = [
            {"role": "system", "content": "You are a helpful assistant."},
        ]

        # Add several conversation turns
        for i in range(3):
            context.append({"role": "user", "content": f"Question {i} about AI"})
            context.append({"role": "assistant", "content": f"Answer {i} about AI"})

        # Add a final question
        final_response = provider.generate_with_context(
            "What is the future of AI?", context
        )

        assert isinstance(final_response, str)
        assert len(final_response) > 0

    @pytest.mark.slow
    def test_response_quality_assessment(self, provider: OpenRouterProvider):
        """Test response quality across different models."""
        models_and_prompts = [
            ("google/gemini-flash-1.5", "Explain machine learning in simple terms."),
            ("meta-llama/llama-3.1-8b-instruct", "What is recursion in programming?"),
            ("mistralai/mistral-7b-instruct", "Write a short poem about technology."),
        ]

        quality_scores = {}

        for model, prompt in models_and_prompts:
            provider.model = model

            response = provider.generate(prompt)

            # Basic quality metrics
            quality_score = 0

            # Length check (should be substantial but not excessive)
            if 20 < len(response) < 2000:
                quality_score += 1

            # Relevance check (should contain relevant terms)
            prompt_lower = prompt.lower()
            response_lower = response.lower()

            if (
                any(term in response_lower for term in ["machine", "learning", "ai"])
                and "machine learning" in prompt_lower
            ):
                quality_score += 1
            elif (
                any(
                    term in response_lower for term in ["recursion", "function", "call"]
                )
                and "recursion" in prompt_lower
            ):
                quality_score += 1
            elif (
                any(
                    term in response_lower
                    for term in ["technology", "tech", "computer"]
                )
                and "technology" in prompt_lower
            ):
                quality_score += 1

            # Coherence check (shouldn't contain obvious errors)
            if "error" not in response_lower[:100]:
                quality_score += 1

            quality_scores[model] = quality_score

        # All models should achieve reasonable quality scores
        for model, score in quality_scores.items():
            assert score >= 2, f"{model} quality score too low: {score}/3"

    @pytest.mark.slow
    def test_cross_provider_consistency(
        self, provider: OpenRouterProvider, api_key: str
    ):
        """Test consistency with other providers for comparison."""
        from devsynth.application.llm.providers import get_llm_provider

        # Test the same prompt with OpenRouter and compare structure
        prompt = "What is the Fibonacci sequence?"

        # Test OpenRouter
        provider.model = "google/gemini-flash-1.5"
        openrouter_response = provider.generate(prompt)

        # Test with a mock other provider for structure comparison
        # Note: This would ideally test against real other providers
        # but for now we just verify OpenRouter returns proper structure

        assert isinstance(openrouter_response, str)
        assert len(openrouter_response) > 0
        assert (
            "fibonacci" in openrouter_response.lower()
            or "sequence" in openrouter_response.lower()
        )


class TestOpenRouterIntegrationEdgeCases:
    """Test edge cases with live OpenRouter API."""

    @pytest.fixture(scope="class")
    def api_key(self) -> str:
        """Get OpenRouter API key."""
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            pytest.skip("OPENROUTER_API_KEY not set")
        return api_key

    @pytest.mark.slow
    def test_very_long_prompt_handling(self, api_key: str):
        """Test handling of very long prompts."""
        config = {"openrouter_api_key": api_key}
        provider = OpenRouterProvider(config)
        provider.model = "google/gemini-flash-1.5"  # Good context window

        # Create a long prompt that approaches context limits
        long_prompt = "Explain quantum computing in detail. " * 50

        try:
            response = provider.generate(long_prompt)
            assert isinstance(response, str)
            assert len(response) > 0
        except Exception as e:
            # Long prompts might be rejected - this is acceptable
            assert "token" in str(e).lower() or "limit" in str(e).lower()

    @pytest.mark.slow
    def test_unicode_and_special_characters(self, api_key: str):
        """Test handling of Unicode and special characters."""
        config = {"openrouter_api_key": api_key}
        provider = OpenRouterProvider(config)
        provider.model = "google/gemini-flash-1.5"

        unicode_prompt = "Say hello in these languages: English, Chinese (你好), Spanish (¡Hola!), and include emoji 🌟"

        response = provider.generate(unicode_prompt)

        assert isinstance(response, str)
        assert len(response) > 0

        # Check for Unicode content in response
        # This is a basic check - real tests would be more sophisticated
        assert len(response) > 10  # Should contain substantial response

    @pytest.mark.slow
    def test_empty_and_whitespace_prompts(self, api_key: str):
        """Test handling of empty and whitespace-only prompts."""
        config = {"openrouter_api_key": api_key}
        provider = OpenRouterProvider(config)
        provider.model = "google/gemini-flash-1.5"

        # Test empty prompt
        with pytest.raises((OpenRouterConnectionError, OpenRouterModelError)):
            provider.generate("")

        # Test whitespace-only prompt
        with pytest.raises((OpenRouterConnectionError, OpenRouterModelError)):
            provider.generate("   ")

    @pytest.mark.slow
    def test_provider_initialization_with_different_models(self, api_key: str):
        """Test provider initialization with different model configurations."""
        models_to_test = [
            "google/gemini-flash-1.5",
            "meta-llama/llama-3.1-8b-instruct",
            "mistralai/mistral-7b-instruct",
        ]

        for model in models_to_test:
            config = {
                "openrouter_api_key": api_key,
                "openrouter_model": model,
            }

            provider = OpenRouterProvider(config)
            assert provider.model == model

            # Test basic functionality with each model
            response = provider.generate("Model initialization test")
            assert isinstance(response, str)
            assert len(response) > 0


class TestOpenRouterIntegrationPerformance:
    """Test performance characteristics of OpenRouter integration."""

    @pytest.fixture(scope="class")
    def api_key(self) -> str:
        """Get API key."""
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            pytest.skip("OPENROUTER_API_KEY not set")
        return api_key

    @pytest.mark.slow
    def test_latency_benchmarks_across_models(self, api_key: str):
        """Benchmark latency across different models."""
        models = [
            "google/gemini-flash-1.5",
            "meta-llama/llama-3.1-8b-instruct",
            "mistralai/mistral-7b-instruct",
        ]

        latency_results = {}

        for model in models:
            config = {"openrouter_api_key": api_key, "openrouter_model": model}
            provider = OpenRouterProvider(config)

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

            latency_results[model] = {
                "avg": avg_latency,
                "max": max_latency,
                "min": min_latency,
                "samples": latencies,
            }

        # Log results for analysis
        for model, results in latency_results.items():
            print(
                f"{model} latency: avg={results['avg']:.2f}s, "
                f"min={results['min']:.2f}s, max={results['max']:.2f}s"
            )

        # Performance assertions
        for model, results in latency_results.items():
            # Average should be reasonable (< 5s for free tier)
            assert (
                results["avg"] < 5.0
            ), f"{model} average latency too high: {results['avg']}s"

            # Maximum should be acceptable (< 10s)
            assert (
                results["max"] < 10.0
            ), f"{model} max latency too high: {results['max']}s"

            # Should have reasonable consistency
            assert results["max"] < results["avg"] * 3, f"{model} latency too variable"

    @pytest.mark.slow
    def test_throughput_measurement(self, api_key: str):
        """Test throughput capabilities."""
        config = {"openrouter_api_key": api_key}
        provider = OpenRouterProvider(config)
        provider.model = "google/gemini-flash-1.5"

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
            except Exception as e:
                # If we hit rate limits or other errors, stop the test
                if "rate limit" in str(e).lower():
                    break
                else:
                    raise

        elapsed = time.time() - start_time
        requests_per_second = request_count / elapsed if elapsed > 0 else 0

        print(
            f"Throughput: {requests_per_second:.2f} requests/second ({request_count} requests in {elapsed:.2f}s)"
        )

        # Should achieve reasonable throughput (> 1 request per 5 seconds)
        assert request_count > 0, "No requests completed"
        assert (
            requests_per_second > 0.2
        ), f"Throughput too low: {requests_per_second} req/s"
