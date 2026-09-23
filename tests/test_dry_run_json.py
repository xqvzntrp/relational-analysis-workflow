from pathlib import Path
import unittest
from dry_run_json import build_dry_run_document

PACKAGE = Path(__file__).parent / "resources" / "product_bundle_example"

class DryRunJsonTests(unittest.TestCase):
    def test_valid_package_is_ready(self):
        d = build_dry_run_document(PACKAGE / "manifest.csv")
        self.assertEqual(1, d["schema_version"])
        self.assertTrue(d["ready"])
        self.assertFalse(any(d["issues"].values()))

    def test_verbose_contains_analysis_model(self):
        d = build_dry_run_document(PACKAGE / "manifest.csv", verbose=True)
        self.assertEqual(16, d["summary"]["step_count"])
        self.assertTrue(d["steps"])
        self.assertTrue(d["dependencies"])
        self.assertTrue(d["grain"]["declarations"])
        self.assertTrue(d["relation_contracts"])

    def test_unresolved_dependency_is_structured(self):
        d = build_dry_run_document(PACKAGE / "manifest_unresolved_relation.csv")
        self.assertFalse(d["ready"])
        issue = d["issues"]["dependency"][0]
        self.assertEqual("unresolved_relation", issue["problem_type"])
        self.assertIn("step", issue)
        self.assertIn("relation", issue)

if __name__ == "__main__":
    unittest.main()
