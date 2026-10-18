from datetime import date
from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


class DashboardTests(unittest.TestCase):
    def make_app(self):
        app = AppTest.from_file(ROOT / "app.py", default_timeout=30).run()
        self.assert_clean(app)
        return app

    def assert_clean(self, app):
        self.assertFalse(list(app.exception), [error.message for error in app.exception])

    def test_all_analysis_views_render(self):
        app = self.make_app()
        self.assertEqual(app.metric[0].value, "698.812,33")
        self.assertEqual(app.metric[1].value, "149.116")
        self.assertEqual(app.metric[4].value, "6,23%")
        for view in ["Tren", "Gerai", "Produk", "Waktu", "Keputusan", "Data & Audit"]:
            with self.subTest(view=view):
                app.session_state["view"] = view
                app.run()
                self.assert_clean(app)

    def test_store_filter_and_empty_selection_recover(self):
        app = self.make_app()
        app.multiselect(key="stores").set_value(["Astoria"]).run()
        self.assert_clean(app)
        self.assertEqual(app.metric[0].value, "232.243,91")
        self.assertEqual(app.metric[1].value, "50.599")
        app.multiselect(key="stores").set_value([]).run()
        self.assert_clean(app)
        self.assertTrue(any("Tidak ada transaksi" in item.value for item in app.info))
        app.button(key="filter_reset").click().run()
        self.assert_clean(app)
        self.assertEqual(app.metric[0].value, "698.812,33")

    def test_cascading_category_filters_and_reset(self):
        app = self.make_app()
        app.multiselect(key="categories").set_value(["Coffee"]).run()
        self.assert_clean(app)
        self.assertEqual(app.metric[0].value, "269.952,45")
        app.multiselect(key="categories").set_value(app.multiselect(key="categories").options).run()
        self.assert_clean(app)
        self.assertEqual(app.metric[0].value, "698.812,33")
        app.multiselect(key="categories").set_value([]).run()
        self.assert_clean(app)
        app.button(key="filter_reset").click().run()
        self.assert_clean(app)
        self.assertEqual(app.metric[0].value, "698.812,33")

    def test_partial_dates_and_missing_comparator_do_not_fake_growth(self):
        app = self.make_app()
        app.selectbox(key="preset").select("Kustom").run()
        app.date_input(key="dates").set_value((date(2023, 5, 15), date(2023, 6, 15))).run()
        self.assert_clean(app)
        self.assertEqual(app.metric[4].value, "Belum tersedia")
        app.button(key="filter_reset").click().run()
        app.selectbox(key="comparison_mode").select("Periode sebelumnya").run()
        self.assert_clean(app)
        self.assertTrue(any("di luar cakupan" in item.value for item in app.caption))
        self.assertEqual(app.metric[0].delta, "")

    def test_period_comparison_and_target_inputs(self):
        app = self.make_app()
        app.selectbox(key="preset").select("Bulan terakhir").run()
        app.selectbox(key="comparison_mode").select("Periode sebelumnya").run()
        self.assert_clean(app)
        self.assertNotEqual(app.metric[0].delta, "")
        app.session_state["view"] = "Keputusan"
        app.run()
        self.assert_clean(app)
        app.number_input(key="target_transactions").set_value(10.0).run()
        app.number_input(key="target_average").set_value(5.0).run()
        self.assert_clean(app)
        self.assertEqual(app.metric[-1].value, "15,50%")

    def test_transaction_search_resets_out_of_range_page(self):
        app = self.make_app()
        app.session_state["view"] = "Data & Audit"
        app.run()
        app.number_input(key="transaction_page").set_value(20).run()
        app.text_input(key="transaction_search").set_value("produk-yang-tidak-ada").run()
        self.assert_clean(app)
        self.assertEqual(app.number_input(key="transaction_page").value, 1)
        self.assertTrue(any("0 transaksi ditemukan" in item.value for item in app.caption))


if __name__ == "__main__":
    unittest.main()
