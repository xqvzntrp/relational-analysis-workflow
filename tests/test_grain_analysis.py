from pathlib import Path
import unittest

from grain_analysis import analyze_grain
from grain_spec import read_grain_declarations


RESOURCES = Path(__file__).parent / "resources"
PACKAGE = RESOURCES / "product_bundle_example"
BAD_PACKAGE = RESOURCES / "grain_invalid_example"


class GrainAnalysisTests(unittest.TestCase):
    def test_example_grain_declarations_are_read(self):
        declarations, issues = read_grain_declarations(PACKAGE / "manifest.csv")

        self.assertEqual([], issues)
        grain_by_relation = {item.relation: item.keys for item in declarations}

        self.assertEqual(("product_id",), grain_by_relation["source_product"])
        self.assertEqual(
            ("product_id", "attribute_id"),
            grain_by_relation["prepared_product_attribute"],
        )
        self.assertEqual(("bundle_id",), grain_by_relation["review_bundle"])

    def test_review_bundle_reports_grain_change_from_product_bundle(self):
        analysis = analyze_grain(PACKAGE / "manifest.csv")

        transition = next(
            item
            for item in analysis.transitions
            if item.relation == "review_bundle"
            and item.upstream_relation == "prepared_product_bundle"
        )

        self.assertEqual(("bundle_id", "product_id"), transition.upstream_grain)
        self.assertEqual(("bundle_id",), transition.grain)
        self.assertTrue(transition.changed)

    def test_bundle_grain_is_preserved_through_inform_business_report(self):
        analysis = analyze_grain(PACKAGE / "manifest.csv")

        by_relation = {
            item.relation: item.grain
            for item in analysis.steps
        }

        self.assertEqual(("bundle_id",), by_relation["review_bundle"])
        self.assertEqual(("bundle_id",), by_relation["focused_bundle"])
        self.assertEqual(("bundle_id",), by_relation["inform_bundle"])
        self.assertEqual(("bundle_id",), by_relation["business_bundle"])
        self.assertEqual(("bundle_id",), by_relation["report_bundle"])

    def test_duplicate_grain_key_is_reported(self):
        _, issues = read_grain_declarations(BAD_PACKAGE / "manifest.csv")

        self.assertEqual(1, len(issues))
        self.assertEqual("duplicate_grain_key", issues[0].problem_type)


if __name__ == "__main__":
    unittest.main()
