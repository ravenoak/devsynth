#!/usr/bin/env python3
"""
Real LM Studio Integration Test for DevSynth.

This test connects to a running LM Studio instance to verify end-to-end functionality.
Note: This test uses real LM Studio and may take significant time due to machine limitations.

Prerequisites:
1. LM Studio must be running on http://127.0.0.1:1234
2. At least one model must be loaded in LM Studio
3. DevSynth dependencies must be installed

Usage:
    cd /Users/caitlyn/Projects/github.com/ravenoak/devsynth
    poetry run pytest tests/integration/general/test_lmstudio_integration_real.py -v -s
"""

import os
import sys
import tempfile
import requests
from pathlib import Path

# Add the DevSynth source to the path
sys.path.insert(0, '/Users/caitlyn/Projects/github.com/ravenoak/devsynth/src')


def check_lmstudio_availability():
    """Check if LM Studio is running and has models loaded."""
    try:
        response = requests.get('http://127.0.0.1:1234/v1/models', timeout=30)
        if response.status_code == 200:
            models_data = response.json()
            models = models_data.get('data', [])
            if models:
                print(f"✅ LM Studio is running with {len(models)} models available:")
                for model in models[:3]:  # Show first 3 models
                    print(f"   - {model['id']}")
                if len(models) > 3:
                    print(f"   ... and {len(models) - 3} more models")
                return True, models[0]['id']  # Return first model ID
            else:
                print("❌ LM Studio is running but no models are loaded")
                return False, None
        else:
            print(f"❌ LM Studio API returned status code: {response.status_code}")
            return False, None
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to LM Studio: {e}")
        return False, None


def test_real_lmstudio_integration():
    """Test DevSynth with real LM Studio connection."""

    print("🔍 Testing DevSynth with Real LM Studio Integration")
    print("=" * 60)

    # First check if LM Studio is available
    available, first_model = check_lmstudio_availability()
    if not available:
        print("❌ LM Studio is not available. Please start LM Studio and load a model.")
        return False

    # Create a temporary directory for DevSynth data
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Set up environment variables for LM Studio
        env_vars = {
            'DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE': 'true',
            'LM_STUDIO_ENDPOINT': 'http://127.0.0.1:1234',
            'DEVSYNTH_OFFLINE': 'false',
            'DEVSYNTH_CONFIG_FILE': '/tmp/devsynth_lmstudio_test/lmstudio_config.yml',
            'DEVSYNTH_MEMORY_PATH': str(temp_path / 'memory'),
            'DEVSYNTH_CHROMADB_PATH': str(temp_path / 'chromadb'),
            'DEVSYNTH_KUZU_PATH': str(temp_path / 'kuzu'),
        }

        # Apply environment variables
        original_env = {}
        for key, value in env_vars.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value

        try:
            print("1. 📋 Testing configuration loading...")

            # Test configuration loading
            from devsynth.config.settings import get_settings
            settings = get_settings()

            # Verify LM Studio is configured as default provider
            llm_provider = settings["llm_provider"]
            assert llm_provider == 'lmstudio', f"Expected lmstudio, got {llm_provider}"
            print("   ✅ Configuration loaded successfully")

            print("2. 🏭 Testing provider factory...")

            # Test provider factory
            from devsynth.application.llm.provider_factory import ProviderFactory
            factory = ProviderFactory()

            # LM Studio provider should be registered
            assert 'lmstudio' in factory.provider_types, "LM Studio provider not registered"
            print("   ✅ LM Studio provider is registered in factory")

            print("3. 🤖 Testing LM Studio provider initialization...")

            # Test LM Studio provider initialization
            from devsynth.application.llm.lmstudio_provider import LMStudioProvider

            # Initialize provider with real LM Studio (patient with limited machine)
            provider = LMStudioProvider({
                'api_base': 'http://127.0.0.1:1234',
                'model': first_model,  # Use the first available model
                'auto_select_model': False,  # Don't auto-select since we specify the model
                'call_timeout': 120.0,  # Very patient timeout for limited machine
                'max_retries': 2  # Allow some retries
            })

            print(f"   ✅ LM Studio provider initialized with model: {first_model}")

            print("4. 🎯 Testing health check...")

            # Test health check (should pass since LM Studio is running)
            health = provider.health_check()
            assert health == True, "Health check should pass when LM Studio is available"
            print("   ✅ Health check passed")

            print("5. 💬 Testing real text generation...")

            # Test real text generation
            prompt = "Hello! Can you help me understand how DevSynth works with LM Studio?"
            response = provider.generate(prompt)

            assert isinstance(response, str), "Response should be a string"
            assert len(response) > 0, "Response should not be empty"
            assert len(response) > 50, "Response should be substantial (not just a token)"

            print(f"   ✅ Generated real response ({len(response)} chars):")
            print(f"      '{response[:200]}...'")

            print("6. 🔄 Testing context-aware generation...")

            # Test context-aware generation
            context = [
                {"role": "system", "content": "You are a helpful AI assistant for DevSynth development."},
                {"role": "user", "content": "What is DevSynth?"}
            ]

            follow_up_prompt = "Can you explain the LM Studio integration in more detail?"
            response_with_context = provider.generate_with_context(follow_up_prompt, context)

            assert isinstance(response_with_context, str), "Context response should be a string"
            assert len(response_with_context) > 0, "Context response should not be empty"
            assert len(response_with_context) > 50, "Context response should be substantial"

            print(f"   ✅ Generated context response ({len(response_with_context)} chars):")
            print(f"      '{response_with_context[:200]}...'")

            print("7. 📊 Testing model information...")

            # Test model information
            available_models = provider.list_available_models()
            assert len(available_models) > 0, "Should have available models"
            assert any(model['id'] == first_model for model in available_models), "First model should be in list"

            print(f"   ✅ Found {len(available_models)} available models")

            print("8. 🎯 Testing model details...")

            # Test model details
            model_details = provider.get_model_details(first_model)
            assert model_details['id'] == first_model, "Model details should match requested model"

            print(f"   ✅ Retrieved details for model: {first_model}")

            print("\n🎉 All real LM Studio integration tests passed!")
            print("🚀 DevSynth successfully integrated with LM Studio!")

            return True

        except Exception as e:
            print(f"❌ Error during real LM Studio testing: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            # Restore original environment variables
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


def test_lmstudio_models():
    """Test different LM Studio models if available."""

    print("\n🧪 Testing Different LM Studio Models")
    print("=" * 50)

    # Check what models are available
    available, first_model = check_lmstudio_availability()
    if not available:
        print("❌ No models available for testing")
        return True  # Not a failure, just no models to test

    # Create a temporary directory for DevSynth data
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Set up minimal environment
        env_vars = {
            'DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE': 'true',
            'LM_STUDIO_ENDPOINT': 'http://127.0.0.1:1234',
            'DEVSYNTH_CONFIG_FILE': '/tmp/devsynth_lmstudio_test/lmstudio_config.yml',
            'DEVSYNTH_MEMORY_PATH': str(temp_path / 'memory'),
            'DEVSYNTH_CHROMADB_PATH': str(temp_path / 'chromadb'),
            'DEVSYNTH_KUZU_PATH': str(temp_path / 'kuzu'),
        }

        # Apply environment variables
        original_env = {}
        for key, value in env_vars.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value

        try:
            # Get models from LM Studio (patient with limited machine)
            response = requests.get('http://127.0.0.1:1234/v1/models', timeout=30)
            models_data = response.json()
            models = models_data.get('data', [])

            # Filter to coding-capable models
            coding_models = [m for m in models if any(keyword in m['id'].lower() for keyword in ['qwen', 'cod', 'code', 'deepseek', 'mistral'])]

            if not coding_models:
                print("ℹ️  No coding-specific models found, using first available model")
                coding_models = models[:1]  # Use first model if no coding models

            for model in coding_models[:2]:  # Test up to 2 models
                print(f"\n🧠 Testing model: {model['id']}")

                from devsynth.application.llm.lmstudio_provider import LMStudioProvider

                # Initialize provider with this specific model (patient with limited machine)
                provider = LMStudioProvider({
                    'api_base': 'http://127.0.0.1:1234',
                    'model': model['id'],
                    'auto_select_model': False,
                    'temperature': 0.7,
                    'max_tokens': 1000,
                    'call_timeout': 120.0,  # Very patient timeout for limited machine
                    'max_retries': 2  # Allow retries for reliability
                })

                # Test a coding-related prompt
                coding_prompt = f"Using {model['id']}, explain how to implement a simple REST API in Python using FastAPI."
                response = provider.generate(coding_prompt)

                print(f"   ✅ Generated response ({len(response)} chars)")
                if len(response) > 200:
                    print(f"      '{response[:200]}...'")
                else:
                    print(f"      '{response}'")

            print("\n✅ Model testing completed successfully!")
            return True

        except Exception as e:
            print(f"❌ Error during model testing: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            # Restore original environment variables
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


if __name__ == "__main__":
    print("🚀 DevSynth Real LM Studio Integration Test Suite")
    print("=" * 70)

    # Test 1: Real LM Studio integration
    success1 = test_real_lmstudio_integration()

    # Test 2: Test different models
    success2 = test_lmstudio_models()

    if success1 and success2:
        print("\n🎊 All real LM Studio integration tests passed!")
        print("🚀 DevSynth is successfully using LM Studio as an LLM provider!")
        sys.exit(0)
    else:
        print("\n💥 Some real LM Studio integration tests failed!")
        sys.exit(1)
