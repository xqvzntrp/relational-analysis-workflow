from pathlib import Path
import csv
import shutil
import unittest

from executor import execute_manifest
from manifest_validator import validate_manifest


PACKAGE = Path(__file__).parent / "resources" / "product_bundle_example"


class ProductBundleExamplePackageTests(unittest.TestCase):
    def tearDown(self):
        for path in [
            PACKAGE / "artifacts" / "package.duckdb",
            PACKAGE / "exports" / "bundle_report.csv",
        ]:
            path.unlink(missing_ok=True)

    def test_example_manifest_is_structurally_valid(self):
        issues = validate_manifest(PACKAGE / "manifest.csv")
        self.assertEqual([], issues)

    def test_invalid_authority_zone_is_rejected(self):
        issues = validate_manifest(PACKAGE / "manifest_invalid_zone.csv")
        problem_types = {issue.problem_type for issue in issues}
        self.assertIn("invalid_authority_zone", problem_types)

    def test_example_package_runs_end_to_end(self):
        outcome = execute_manifest(PACKAGE / "manifest.csv")

        self.assertEqual([], outcome.validation_issues)
        self.assertIsNone(outcome.execution_issue)
        self.assertEqual(16, len(outcome.results))
        self.assertTrue(all(r.status == "completed" for r in outcome.results))

        actual_path = PACKAGE / "exports" / "bundle_report.csv"
        expected_path = PACKAGE / "specifications" / "expected_report.csv"

        self.assertTrue(actual_path.exists())

        with actual_path.open("r", encoding="utf-8", newline="") as handle:
            actual = list(csv.reader(handle))

        with expected_path.open("r", encoding="utf-8", newline="") as handle:
            expected = list(csv.reader(handle))

        self.assertEqual(expected, actual)

    def test_missing_sql_stops_before_later_steps(self):
        outcome = execute_manifest(PACKAGE / "manifest_missing_sql.csv")

        self.assertEqual([], outcome.validation_issues)
        self.assertIsNotNone(outcome.execution_issue)
        self.assertEqual("2", outcome.execution_issue.step)
        self.assertEqual("run_sql", outcome.execution_issue.mode)
        self.assertEqual(1, len(outcome.results))


if __name__ == "__main__":
    unittest.main()
