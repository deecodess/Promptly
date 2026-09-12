import unittest

from token_counter import count_tokens, token_delta


class TokenCounterTests(unittest.TestCase):
    def test_empty_text_has_zero_tokens(self):
        self.assertEqual(count_tokens(""), 0)

    def test_counts_non_empty_text(self):
        self.assertGreater(count_tokens("Compress this prompt."), 0)

    def test_token_delta_reports_savings(self):
        metrics = token_delta("one two three four", "one two")
        self.assertGreater(metrics["original_tokens"], metrics["compressed_tokens"])
        self.assertGreater(metrics["saved_tokens"], 0)
        self.assertGreater(metrics["reduction_pct"], 0)


if __name__ == "__main__":
    unittest.main()
