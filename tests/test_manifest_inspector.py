from pathlib import Path
import unittest

from manifest_inspector import inspect_manifest


FIXTURES = Path(__file__).parent / "fixtures"


class ManifestInspectorTests(unittest.TestCase):
    def test_inspection_preserves_manifest_order(self):
        rows = inspect_manifest(FIXTURES / "valid_manifest.csv")
        self.assertEqual(["1", "2", "3"], [row.step for row in rows])
        self.assertEqual("load_csv", rows[0].mode)
        self.assertEqual("source", rows[0].authority_zone)

    def test_relative_paths_resolve_from_manifest_directory(self):
        rows = inspect_manifest(FIXTURES / "valid_manifest.csv")
        self.assertTrue(rows[0].resolved_input.endswith("tests/fixtures/data/product.csv"))
        self.assertTrue(rows[2].resolved_output.endswith("tests/fixtures/artifacts/product.csv"))


if __name__ == "__main__":
    unittest.main()
