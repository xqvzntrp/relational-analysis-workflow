from pathlib import Path
import unittest

from dependency_discovery import discover_sql_dependencies
from dependency_plan import discover_manifest_dependencies


PACKAGE = Path(__file__).parent / "resources" / "product_bundle_example"


class DependencyDiscoveryTests(unittest.TestCase):
    def test_review_sql_discovers_created_and_referenced_relations(self):
        deps = discover_sql_dependencies(PACKAGE / "sql" / "review_bundle.sql")

        self.assertEqual(("review_bundle",), deps.creates)
        self.assertEqual(
            (
                "prepared_bundle",
                "prepared_product_bundle",
                "prepared_product",
            ),
            deps.references,
        )

    def test_manifest_dependency_plan_includes_source_and_sql_steps(self):
        plan = discover_manifest_dependencies(PACKAGE / "manifest.csv")

        self.assertEqual(16, len(plan))

        self.assertEqual(("source_product",), plan[0].creates)
        self.assertEqual((), plan[0].references)

        review = next(item for item in plan if item.step == "11")
        self.assertEqual(("review_bundle",), review.creates)
        self.assertIn("prepared_bundle", review.references)
        self.assertIn("prepared_product_bundle", review.references)
        self.assertIn("prepared_product", review.references)

        export = next(item for item in plan if item.step == "16")
        self.assertEqual(("report_bundle",), export.references)


if __name__ == "__main__":
    unittest.main()
