"""Checks of accounting, textbook reproduction, sampling and input changes."""

from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import random
import unittest

from simulate import (choose_best, daily_result, demand_distribution, exact_metrics,
                      experiment, generate_days, pick, stock_options, validate)


def config():
    return json.loads(Path(__file__).with_name("config.json").read_text())


class InventoryTests(unittest.TestCase):
    def test_hand_case_demand_below_stock(self):
        result = daily_result(70, 50, config())
        self.assertEqual(result, dict(sold=50, unsold=20, unmet=0, revenue=2500,
                         purchase_cost=2100, recovery=200, unmet_deduction=0,
                         cash_profit=600, textbook_score=600))

    def test_hand_case_demand_equals_stock(self):
        result = daily_result(70, 70, config())
        self.assertEqual((result["unsold"], result["unmet"], result["cash_profit"],
                          result["textbook_score"]), (0, 0, 1400, 1400))

    def test_hand_case_demand_above_stock(self):
        result = daily_result(70, 90, config())
        self.assertEqual((result["sold"], result["unmet"], result["unmet_deduction"],
                          result["cash_profit"], result["textbook_score"]),
                         (70, 20, 400, 1400, 1000))

    def test_zero_stock(self):
        result = daily_result(0, 40, config())
        self.assertEqual((result["sold"], result["cash_profit"],
                          result["textbook_score"]), (0, 0, -800))

    def test_zero_demand(self):
        result = daily_result(70, 0, config())
        self.assertEqual((result["recovery"], result["cash_profit"]), (700, -1400))

    def test_negative_stock_or_demand_rejected(self):
        for stock, demand in [(-1, 40), (70, -1)]:
            with self.subTest(stock=stock, demand=demand), self.assertRaises(ValueError):
                daily_result(stock, demand, config())

    def test_textbook_ten_day_total(self):
        # Source PDF pp. 69-71: dollars expressed as integer cents here.
        c = config()
        c.update(unit_cost=33, selling_price=50, salvage_value=5)
        demand = [80, 80, 70, 50, 80, 70, 90, 60, 40, 40]
        totals = {key: sum(daily_result(70, d, c)[key] for d in demand)
                  for key in ["revenue", "purchase_cost", "unmet_deduction",
                              "recovery", "textbook_score"]}
        self.assertEqual(totals, dict(revenue=30500, purchase_cost=23100,
                         unmet_deduction=850, recovery=450, textbook_score=7000))

    def test_all_day_digit_assignments(self):
        c = config()
        counts = Counter(pick(c["day_types"], c["day_type_percent"], roll)
                         for roll in range(1, 101))
        self.assertEqual(counts, Counter(dict(zip(c["day_types"], c["day_type_percent"]))))

    def test_all_conditional_digit_assignments(self):
        c = config()
        for row in c["demand_percent_by_type"]:
            counts = Counter(pick(c["demand_values"], row, roll) for roll in range(1, 101))
            self.assertEqual([counts[d] for d in c["demand_values"]], row)

    def test_digit_boundaries_and_zero_probability(self):
        c = config()
        self.assertEqual([pick(c["day_types"], c["day_type_percent"], r)
                          for r in [1, 35, 36, 80, 81, 100]],
                         ["Busy", "Busy", "Normal", "Normal", "Quiet", "Quiet"])
        self.assertEqual(pick(c["demand_values"], c["demand_percent_by_type"][2], 100), 80)
        for r in [0, 101]:
            with self.assertRaises(ValueError):
                pick(c["day_types"], c["day_type_percent"], r)

    def test_invalid_probabilities_rejected(self):
        c = config()
        for percentages in [[35, 44, 20], [101, -1, 0], [True, 45, 54]]:
            with self.subTest(percentages=percentages):
                bad = deepcopy(c)
                bad["day_type_percent"] = percentages
                with self.assertRaises(ValueError):
                    validate(bad)

    def test_invalid_economics_rejected(self):
        for changes in [dict(unit_cost=0), dict(selling_price=30), dict(salvage_value=31)]:
            c = config()
            c.update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate(c)

    def test_invalid_structure_and_experiment_settings_rejected(self):
        for changes in [dict(runs=1), dict(days_per_run=0), dict(bundle_size=0),
                        dict(demand_values=[50, 40]), dict(day_types=["Busy", "Busy", "Quiet"]),
                        dict(audit_days=1001), dict(demand_percent_by_type=[[100]]),
                        dict(stock_min=-1), dict(stock_min=500, stock_max=100), dict(stock_max="500")]:
            c = config()
            c.update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate(c)

    def test_stock_range_adapts_to_support_and_bundle(self):
        c = config()
        self.assertEqual(stock_options(c), list(range(0, 101, 10)))
        c["demand_values"] = [0, 17, 43]
        self.assertEqual(stock_options(c), [0, 10, 20, 30, 40, 50])
        c.update(stock_min=200, stock_max=500, bundle_size=50)
        self.assertEqual(stock_options(c), [200, 250, 300, 350, 400, 450, 500])
        self.assertEqual(daily_result(500, 70, c)["cash_profit"], -7200)
        c.update(stock_min=500, stock_max=500)
        self.assertEqual(stock_options(c), [500])

    def test_marginal_distribution_matches_hand_calculation(self):
        expected = [0.1435, 0.1425, 0.2645, 0.184, 0.1705, 0.0705, 0.0245]
        self.assertEqual([p for _, p in demand_distribution(config())], expected)
        self.assertAlmostEqual(sum(expected), 1)

    def test_exact_expectation_by_exhaustive_digit_pairs(self):
        # An independent oracle: all 100 x 100 equally likely digit pairs.
        c = config()
        days = []
        for first in range(1, 101):
            i = pick(range(3), c["day_type_percent"], first)
            days.extend(pick(c["demand_values"], c["demand_percent_by_type"][i], second)
                        for second in range(1, 101))
        for q in stock_options(c):
            # Express the accounting differently from daily_result.
            scores = [50 * min(q, d) + 10 * max(q - d, 0) - 30 * q
                      - 20 * max(d - q, 0) for d in days]
            self.assertAlmostEqual(sum(scores) / len(scores),
                                   exact_metrics(q, c)["textbook_score"])

    def test_fixed_seed_reproduces_trace(self):
        c = config()
        self.assertEqual(generate_days(c, 123), generate_days(c, 123))

    def test_next_seed_changes_trace(self):
        c = config()
        self.assertNotEqual(generate_days(c, 123), generate_days(c, 124))

    def test_local_rng_does_not_change_global_rng(self):
        random.seed(99)
        state = random.getstate()
        generate_days(config(), 123)
        self.assertEqual(state, random.getstate())

    def test_deterministic_demand_matches_exact_for_every_stock(self):
        c = config()
        c.update(demand_values=[40], demand_percent_by_type=[[100], [100], [100]],
                 runs=3, days_per_run=20)
        summary, _, _, _, _ = experiment(c)
        for row in summary:
            self.assertEqual(row["sim_textbook_score"], row["exact_textbook_score"])
            self.assertEqual(row["score_standard_error"], 0)

    def test_shared_trace_accounting_and_run_counts(self):
        c = config()
        c.update(runs=2, days_per_run=20)
        _, per_run, trace, _, metadata = experiment(c)
        self.assertEqual((len(trace), len(per_run), metadata["stock_day_evaluations"]),
                         (40, 22, 440))
        for row in per_run:
            days = [d for d in trace if d["run"] == row["run"]]
            expected = sum(daily_result(row["stock"], d["demand"], c)["textbook_score"]
                           for d in days) / len(days)
            self.assertEqual(row["textbook_score"], expected)

    def test_price_change_recalculates_winner(self):
        c = config()
        original = [dict(stock=q, score=exact_metrics(q, c)["textbook_score"])
                    for q in stock_options(c)]
        c["selling_price"] = 80
        changed = [dict(stock=q, score=exact_metrics(q, c)["textbook_score"])
                   for q in stock_options(c)]
        self.assertEqual(choose_best(original, "score"), [70])
        self.assertEqual(choose_best(changed, "score"), [80])

    def test_objective_choice_changes_recommendation(self):
        rows = [dict(stock=q, **exact_metrics(q, config())) for q in stock_options(config())]
        self.assertEqual(choose_best(rows, "textbook_score"), [70])
        self.assertEqual(choose_best(rows, "cash_profit"), [60])

    def test_ties_are_reported(self):
        self.assertEqual(choose_best([dict(stock=40, score=5), dict(stock=50, score=5)],
                                     "score"), [40, 50])


if __name__ == "__main__":
    unittest.main(verbosity=2)
