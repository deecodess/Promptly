import unittest

from compressor import compress_prompt, normalize_text
from evaluator import preservation_score


LONG_PROMPT = """
Please note that you are helping with a launch plan. Please note that you are helping with a launch plan.
The plan must include engineering tasks, QA, analytics, support readiness, and rollout.
It is important to note that the team has two weeks.
Do not suggest a full rewrite.
Include acceptance criteria and tests.
There are many extra details about meetings and general coordination that are useful but lower priority.
There are many extra details about meetings and general coordination that are useful but lower priority.
Output markdown with sections for Summary, Risks, Tests, and Rollout.
"""


class CompressorTests(unittest.TestCase):
    def test_normalize_text_collapses_spacing(self):
        self.assertEqual(normalize_text("  hello   world  "), "hello world")

    def test_compression_is_shorter_and_non_empty(self):
        result = compress_prompt(LONG_PROMPT, "balanced")
        self.assertTrue(result.compressed)
        self.assertLess(result.compressed_tokens, result.original_tokens)
        self.assertGreater(result.reduction_pct, 0)

    def test_modes_become_more_aggressive(self):
        conservative = compress_prompt(LONG_PROMPT, "conservative")
        aggressive = compress_prompt(LONG_PROMPT, "aggressive")
        self.assertLessEqual(aggressive.compressed_tokens, conservative.compressed_tokens)

    def test_preserves_important_constraints(self):
        result = compress_prompt(LONG_PROMPT, "balanced")
        self.assertIn("must include", result.compressed.lower())
        self.assertIn("do not", result.compressed.lower())
        self.assertGreaterEqual(preservation_score(LONG_PROMPT, result.compressed), 70)

    def test_empty_prompt(self):
        result = compress_prompt("", "balanced")
        self.assertEqual(result.compressed, "")
        self.assertEqual(result.original_tokens, 0)


if __name__ == "__main__":
    unittest.main()
