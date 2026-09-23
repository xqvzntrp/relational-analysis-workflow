from pathlib import Path
import tempfile
import unittest
from artifact_checker import check_artifact
from artifact_spec import ArtifactExpectation, read_artifact_expectations

PACKAGE = Path(__file__).parent / "resources" / "product_bundle_example"

class ArtifactCheckerTests(unittest.TestCase):
    def test_example_expectation_is_declared(self):
        expectations, issues = read_artifact_expectations(PACKAGE / "manifest.csv")
        self.assertEqual([], issues)
        self.assertEqual("exports/bundle_report.csv", expectations[0].artifact)

    def test_matching_csv(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root/"a.csv").write_text("id,value\n1,A\n", encoding="utf-8")
            (root/"e.csv").write_text("id,value\n1,A\n", encoding="utf-8")
            result = check_artifact(root, ArtifactExpectation("a.csv","e.csv"))
            self.assertTrue(result.matches)
            self.assertEqual(result.artifact_sha256, result.expected_sha256)

    def test_readable_csv_diff(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root/"a.csv").write_text("id,value\n1,B\n", encoding="utf-8")
            (root/"e.csv").write_text("id,value\n1,A\n", encoding="utf-8")
            result = check_artifact(root, ArtifactExpectation("a.csv","e.csv"))
            self.assertFalse(result.matches)
            self.assertIn("row 2:", result.details[0])
            self.assertIn("'A'", result.details[0])
            self.assertIn("'B'", result.details[0])

if __name__ == "__main__":
    unittest.main()
