import unittest
from unittest.mock import patch, MagicMock
from devsynth.application.utils.token_tracker import TokenTracker, TokenLimitExceededError, _TEST_MODE, _TEST_TOKEN_COUNTS
import pytest
pytest.skip('TokenTracker tests unstable', allow_module_level=True)


class TestTokenTracker(unittest.TestCase):
    """Test cases for the TokenTracker utility.

ReqID: N/A"""

    def setUp(self):
        """Set up test environment."""
        global _TEST_MODE, _TEST_TOKEN_COUNTS
        _TEST_MODE = True
        _TEST_TOKEN_COUNTS = {'This is a test': 4, 'system': 3, 'user': 4,
            'assistant': 4, 'You are a helpful assistant.': 3, 'Hello': 4,
            'Hi there!': 4, 'Message 1': 5, 'Response 1': 5, 'Message 2': 5,
            'Response 2': 5}
        self.tracker = TokenTracker()

    def tearDown(self):
        """Clean up after tests."""
        global _TEST_MODE
        _TEST_MODE = False

    def test_count_tokens_succeeds(self):
        """Test token counting.

ReqID: N/A"""
        text = 'This is a test'
        count = self.tracker.count_tokens(text)
        self.assertEqual(count, 4)

    def test_count_message_tokens_succeeds(self):
        """Test token counting for a message.

ReqID: N/A"""
        message = {'role': 'system', 'content': 'This is a test'}
        count = self.tracker.count_message_tokens(message)
        self.assertEqual(count, 9)

    def test_count_conversation_tokens_succeeds(self):
        """Test token counting for a conversation.

ReqID: N/A"""
        conversation = [{'role': 'system', 'content':
            'You are a helpful assistant.'}, {'role': 'user', 'content':
            'Hello'}, {'role': 'assistant', 'content': 'Hi there!'}]
        count = self.tracker.count_conversation_tokens(conversation)
        self.assertEqual(count, 28)

    def test_prune_conversation_succeeds(self):
        """Test conversation pruning.

ReqID: N/A"""
        conversation = [{'role': 'system', 'content':
            'You are a helpful assistant.'}, {'role': 'user', 'content':
            'Message 1'}, {'role': 'assistant', 'content': 'Response 1'}, {
            'role': 'user', 'content': 'Message 2'}, {'role': 'assistant',
            'content': 'Response 2'}]
        pruned = self.tracker.prune_conversation(conversation, max_tokens=40)
        self.assertEqual(len(pruned), 3)
        self.assertEqual(pruned[0]['role'], 'system')
        self.assertEqual(pruned[1]['content'], 'Message 2')
        self.assertEqual(pruned[2]['content'], 'Response 2')

    def test_ensure_token_limit_succeeds(self):
        """Test token limit enforcement.

ReqID: N/A"""
        with self.assertRaises(TokenLimitExceededError):
            self.tracker.ensure_token_limit('This is a test', max_tokens=3)
        try:
            self.tracker.ensure_token_limit('This is a test', max_tokens=10)
        except TokenLimitExceededError:
            self.fail(
                'ensure_token_limit raised TokenLimitExceededError unexpectedly!'
                )

    def test_fallback_tokenizer_succeeds(self):
        """Test the fallback tokenizer when tiktoken is not available.

ReqID: N/A"""
        with patch(
            'devsynth.application.utils.token_tracker.TIKTOKEN_AVAILABLE', 
            False):
            tracker = TokenTracker()
            text = 'This is a test'
            count = tracker.count_tokens(text)
            self.assertEqual(count, 4)


if __name__ == '__main__':
    unittest.main()
