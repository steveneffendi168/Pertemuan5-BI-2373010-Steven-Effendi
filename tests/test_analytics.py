import json
from pathlib import Path
import unittest

import pandas as pd

from coffee_analytics import (
    breakdown, compare_breakdown, daily_summary, filter_data, growth,
    hourly_profile, monthly_summary, previous_period, product_summary,
    scenario, summarize, trend_summary,
)

ROOT = Path(__file__).resolve().parents[1]


class AnalyticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = pd.read_csv(ROOT / "data_prepared" / "coffee_sales_prepared.csv")
        cls.data["transaction_date"] = pd.to_datetime(cls.data["transaction_date"])
        cls.source_dates = cls.data["transaction_date"].unique()
        cls.audit = json.loads((ROOT / "data_prepared" / "audit_report.json").read_text())

    def test_totals_reconcile_with_audit(self):
        result = summarize(self.data)
        self.assertAlmostEqual(result["total_sales"], self.audit["total_sales"], places=2)
        self.assertEqual(result["total_transactions"], 149116)
        self.assertEqual(result["total_units"], 214470)

    def test_monthly_matches_prepared_summary(self):
        result = monthly_summary(self.data, "2023-01-01", "2023-06-30", self.source_dates)
        expected = pd.read_csv(ROOT / "data_prepared" / "monthly_summary.csv")
        for metric in ["total_sales", "total_transactions", "total_units", "growth_pct"]:
            pd.testing.assert_series_equal(result[metric], expected[metric], check_dtype=False)
        self.assertTrue(result["coverage"].eq("Penuh").all())

    def test_partial_month_is_not_compared_with_full_month(self):
        selected = self.data.loc[self.data["transaction_date"].between("2023-01-15", "2023-02-28")]
        result = monthly_summary(selected, "2023-01-15", "2023-02-28", self.source_dates)
        self.assertTrue(result["growth_pct"].isna().all())
        self.assertEqual(result.iloc[1]["coverage"], "Penuh")

    def test_missing_source_day_prevents_full_month_growth(self):
        dates = [day for day in self.source_dates if pd.Timestamp(day) != pd.Timestamp("2023-05-15")]
        result = monthly_summary(self.data, "2023-05-01", "2023-06-30", dates)
        self.assertTrue(result["growth_pct"].isna().all())

    def test_empty_month_keeps_calendar_gap(self):
        selected = self.data.loc[self.data["month"].ne("2023-02")]
        result = monthly_summary(selected, "2023-01-01", "2023-03-31", self.source_dates)
        self.assertEqual(result.iloc[1]["total_sales"], 0)
        self.assertTrue(pd.isna(result.iloc[2]["growth_pct"]))
        self.assertAlmostEqual(result.iloc[1]["growth_pct"], -100)

    def test_all_dimensions_and_inclusive_boundaries(self):
        sample = self.data.iloc[0]
        date = sample["transaction_date"]
        result = filter_data(self.data, date, date,
                             [sample["store_location"]], [sample["product_category"]],
                             [sample["product_type"]], [sample["product_id"]],
                             [sample["day_of_week"]], (sample["hour"], sample["hour"]))
        self.assertIn(sample["transaction_id"], result["transaction_id"].tolist())
        self.assertEqual(result["product_id"].nunique(), 1)
        self.assertEqual(result["transaction_date"].nunique(), 1)

    def test_daily_and_weekly_preserve_total_sales(self):
        daily = daily_summary(self.data, "2023-01-01", "2023-06-30")
        weekly = trend_summary(self.data, "2023-01-01", "2023-06-30", "W-SUN")
        self.assertEqual(len(daily), 181)
        self.assertAlmostEqual(daily["total_sales"].sum(), 698812.33, places=2)
        self.assertAlmostEqual(weekly["total_sales"].sum(), 698812.33, places=2)

    def test_previous_period_same_inclusive_length(self):
        start, end = previous_period("2023-06-01", "2023-06-30")
        self.assertEqual(str(start), "2023-05-02")
        self.assertEqual(str(end), "2023-05-31")
        start, end = previous_period("2023-03-01", "2023-03-01")
        self.assertEqual(str(start), "2023-02-28")
        self.assertEqual(start, end)

    def test_product_shares_and_weighted_prices(self):
        products = product_summary(self.data)
        self.assertAlmostEqual(products["sales_share"].sum(), 100)
        self.assertAlmostEqual(products.iloc[-1]["cumulative_share"], 100)
        self.assertEqual(products.iloc[0]["product_id"], 61)
        for row in products.to_dict("records"):
            self.assertAlmostEqual(row["weighted_unit_price"], row["total_sales"] / row["total_units"])

    def test_comparison_keeps_disappearing_group_and_undefined_ratios(self):
        current = self.data.loc[self.data["store_location"].eq("Astoria")]
        previous = self.data.loc[self.data["store_location"].eq("Lower Manhattan")]
        result = compare_breakdown(breakdown(current, ["store_location"]), previous, ["store_location"])
        disappeared = result.loc[result["store_location"].eq("Lower Manhattan")].iloc[0]
        new = result.loc[result["store_location"].eq("Astoria")].iloc[0]
        self.assertEqual(disappeared["growth_pct"], -100)
        self.assertTrue(pd.isna(disappeared["average_transaction_value"]))
        self.assertTrue(pd.isna(new["growth_pct"]))

    def test_normalization_uses_calendar_occurrences(self):
        profile = hourly_profile(self.data, "2023-01-01", "2023-06-30", list(range(7)), (6, 20), True)
        mondays = int((pd.date_range("2023-01-01", "2023-06-30").dayofweek == 0).sum())
        count = self.data.loc[self.data["day_of_week"].eq(0) & self.data["hour"].eq(10), "transaction_id"].nunique()
        self.assertAlmostEqual(profile.loc["Senin", "10:00"], count / mondays)

    def test_zero_denominator_and_compounded_scenario(self):
        self.assertIsNone(growth(100, 0))
        self.assertIsNone(growth(100, None))
        result = scenario(1000, 5, 3)
        self.assertAlmostEqual(result["projected_sales"], 1081.5)
        self.assertAlmostEqual(result["growth_pct"], 8.15)
        self.assertEqual(scenario(1000, -100, 3)["projected_sales"], 0)


if __name__ == "__main__":
    unittest.main()
