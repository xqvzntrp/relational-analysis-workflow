from pathlib import Path
import csv
import shutil
import unittest

import duckdb

from executor import database_path_for_manifest, execute_manifest


FIXTURES = Path(__file__).parent / "fixtures"


class ExecutorTests(unittest.TestCase):
    def tearDown(self):
        artifacts = FIXTURES / "artifacts"
        if artifacts.exists():
            shutil.rmtree(artifacts)

    def test_valid_manifest_executes_all_three_modes(self):
        manifest = FIXTURES / "valid_manifest.csv"
        results, issues = execute_manifest(manifest)

        self.assertEqual([], issues)
        self.assertEqual(3, len(results))
        self.assertTrue(all(result.status == "completed" for result in results))

        database_path = database_path_for_manifest(manifest)
        self.assertTrue(database_path.exists())

        connection = duckdb.connect(str(database_path), read_only=True)
        try:
            rows = connection.execute(
                "SELECT product_id, product_name_upper "
                "FROM prepared_product ORDER BY product_id"
            ).fetchall()
        finally:
            connection.close()

        self.assertEqual(
            [("P001", "SOFA"), ("P002", "COFFEE TABLE")],
            rows,
        )

        export_path = FIXTURES / "artifacts" / "product.csv"
        self.assertTrue(export_path.exists())

        with export_path.open("r", encoding="utf-8", newline="") as handle:
            exported = list(csv.reader(handle))

        self.assertEqual(
            [
                ["product_id", "product_name", "product_name_upper"],
                ["P001", "Sofa", "SOFA"],
                ["P002", "Coffee Table", "COFFEE TABLE"],
            ],
            exported,
        )

    def test_invalid_manifest_never_builds_execution_plan(self):
        results, issues = execute_manifest(FIXTURES / "invalid_manifest.csv")

        self.assertEqual([], results)
        self.assertTrue(issues)


if __name__ == "__main__":
    unittest.main()
