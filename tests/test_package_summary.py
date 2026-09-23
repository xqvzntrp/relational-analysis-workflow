from pathlib import Path
import unittest

from package_summary import summarize_package


PACKAGE = Path(__file__).parent / "resources" / "product_bundle_example"


class PackageSummaryTests(unittest.TestCase):
    def test_example_package_summary(self):
        summary = summarize_package(PACKAGE / "manifest.csv")

        self.assertEqual(16, summary.step_count)
        self.assertEqual(5, summary.mode_counts["load_csv"])
        self.assertEqual(10, summary.mode_counts["run_sql"])
        self.assertEqual(1, summary.mode_counts["export_sql"])

        self.assertEqual(5, summary.authority_zone_counts["source"])
        self.assertEqual(5, summary.authority_zone_counts["prepared"])
        self.assertEqual(1, summary.authority_zone_counts["review"])
        self.assertEqual(1, summary.authority_zone_counts["focused"])
        self.assertEqual(1, summary.authority_zone_counts["inform"])
        self.assertEqual(1, summary.authority_zone_counts["business"])
        self.assertEqual(2, summary.authority_zone_counts["report"])

        self.assertIn("source_product", summary.created_relations)
        self.assertIn("report_bundle", summary.created_relations)
        self.assertEqual(
            ("exports/bundle_report.csv",),
            summary.export_outputs,
        )


if __name__ == "__main__":
    unittest.main()
