class Counter:
    """Utility class to count words, lines, and characters."""

    def count_lines(self, text: str) -> int:
        return len(text.splitlines())

    def count_words(self, text: str) -> int:
        return len(text.split())

    def count_chars(self, text: str) -> int:
        return len(text)
