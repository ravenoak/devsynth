from counter import Counter


def test_counts():
    text = "hello world\nthis is a test"
    counter = Counter()
    assert counter.count_lines(text) == 2
    assert counter.count_words(text) == 5
    assert counter.count_chars(text) == len(text)
