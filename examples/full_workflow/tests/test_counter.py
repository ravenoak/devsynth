import os
import sys

import pytest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from counter import Counter

pytestmark = [pytest.mark.fast]


def test_counts():
    text = "hello world\nthis is a test"
    counter = Counter()
    assert counter.count_lines(text) == 2
    assert counter.count_words(text) == 6
    assert counter.count_chars(text) == len(text)
