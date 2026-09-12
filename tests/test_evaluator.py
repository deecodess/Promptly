import unittest
from pathlib import Path

from evaluator import benchmark, evaluate_prompt, load_prompts


class EvaluatorTests(unittest.TestCase):
    def test_loads_benchmark_prompts(self):
        prompts = load_prompts(Path("examples") / "benchmark_prompts.json")
        self.assertGreaterEqual(len(prompts), 20)

    def test_evaluate_prompt_outputs_resume_metrics(self):
        prompt = {
            "id": "test",
            "category": "coding",
            "prompt": "You must include tests. You must include tests. Do not remove API details. Add rollout steps.",
        }
        result = evaluate_prompt(prompt)
        self.assertEqual(result.prompt_id, "test")
        self.assertGreaterEqual(result.preservation_score, 50)
        self.assertGreaterEqual(result.latency_ms, 0)

    def test_benchmark_summary(self):
        prompts = load_prompts(Path("examples") / "benchmark_prompts.json")[:3]
        report = benchmark(prompts)
        self.assertEqual(report["summary"]["prompt_count"], 3)
        self.assertIn("avg_reduction_pct", report["summary"])
        self.assertIn("results", report)


if __name__ == "__main__":
    unittest.main()
