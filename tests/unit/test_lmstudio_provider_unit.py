
import unittest
from unittest.mock import patch, MagicMock
import json
import os
from devsynth.application.llm.lmstudio_provider import LMStudioProvider
from devsynth.application.utils.token_tracker import TokenTracker, TokenLimitExceededError

class TestLMStudioProvider(unittest.TestCase):
    """Test cases for the LMStudio LLM provider."""
    
    def setUp(self):
        """Set up test environment."""
        self.config = {
            "api_base": "http://localhost:1234/v1",
            "model": "local_model"
        }
        self.provider = LMStudioProvider(self.config)
    
    @patch('requests.post')
    def test_generate(self, mock_post):
        """Test the generate method."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "This is a test response"
                    }
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # Call the method
        result = self.provider.generate("Test prompt")
        
        # Verify the result
        self.assertEqual(result, "This is a test response")
        
        # Verify the API call
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "http://localhost:1234/v1/chat/completions")
        
        # Verify the request payload
        payload = json.loads(kwargs['data'])
        self.assertEqual(payload['model'], "local_model")
        self.assertEqual(len(payload['messages']), 1)
        self.assertEqual(payload['messages'][0]['role'], "user")
        self.assertEqual(payload['messages'][0]['content'], "Test prompt")
    
    @patch('requests.post')
    def test_generate_with_context(self, mock_post):
        """Test the generate_with_context method."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "This is a test response with context"
                    }
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # Context
        context = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        # Call the method
        result = self.provider.generate_with_context("How are you?", context)
        
        # Verify the result
        self.assertEqual(result, "This is a test response with context")
        
        # Verify the API call
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "http://localhost:1234/v1/chat/completions")
        
        # Verify the request payload
        payload = json.loads(kwargs['data'])
        self.assertEqual(payload['model'], "local_model")
        self.assertEqual(len(payload['messages']), 4)  # 3 from context + 1 new
        self.assertEqual(payload['messages'][0]['role'], "system")
        self.assertEqual(payload['messages'][1]['role'], "user")
        self.assertEqual(payload['messages'][2]['role'], "assistant")
        self.assertEqual(payload['messages'][3]['role'], "user")
        self.assertEqual(payload['messages'][3]['content'], "How are you?")
    
    @patch('requests.post')
    def test_get_embedding(self, mock_post):
        """Test the get_embedding method."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "embedding": [0.1, 0.2, 0.3, 0.4, 0.5]
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # Call the method
        result = self.provider.get_embedding("Test text")
        
        # Verify the result
        self.assertEqual(result, [0.1, 0.2, 0.3, 0.4, 0.5])
        
        # Verify the API call
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "http://localhost:1234/v1/embeddings")
        
        # Verify the request payload
        payload = json.loads(kwargs['data'])
        self.assertEqual(payload['model'], "local_model")
        self.assertEqual(payload['input'], "Test text")
    
    @patch('requests.post')
    def test_api_error_handling(self, mock_post):
        """Test error handling for API calls."""
        # Mock error response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal server error"}
        mock_post.return_value = mock_response
        
        # Call the method and expect an exception
        with self.assertRaises(Exception):
            self.provider.generate("Test prompt")

if __name__ == '__main__':
    unittest.main()
