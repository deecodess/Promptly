import unittest

from cost_estimator import available_models, estimate_input_cost, estimate_savings, format_usd


class CostEstimatorTests(unittest.TestCase):
    def test_available_models_load_from_config(self):
        self.assertIn("gpt-5.4-mini", available_models())

    def test_estimate_input_cost(self):
        cost = estimate_input_cost(1_000_000, "gpt-5.4-mini")
        self.assertEqual(cost, 0.75)

    def test_estimate_savings_decreases_cost(self):
        savings = estimate_savings(1000, 500, "gpt-5.4-mini")
        self.assertGreater(savings["cost_before"], savings["cost_after"])
        self.assertGreater(savings["cost_saved"], 0)

    def test_format_usd_keeps_small_costs_visible(self):
        self.assertEqual(format_usd(0), "$0.00")
        self.assertTrue(format_usd(0.000123).startswith("$0.000"))


if __name__ == "__main__":
    unittest.main()
