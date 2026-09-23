from pathlib import Path
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

    def test_valid_manifest_executes_load_csv_and_run_sql(self):
        manifest = FIXTURES / "valid_manifest.csv"
        results, issues = execute_manifest(manifest)

        self.assertEqual([], issues)
        self.assertEqual(3, len(results))
        self.assertEqual("completed", results[0].status)
        self.assertEqual("completed", results[1].status)
        self.assertEqual("pending", results[2].status)

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

    def test_invalid_manifest_never_builds_execution_plan(self):
        results, issues = execute_manifest(FIXTURES / "invalid_manifest.csv")

        self.assertEqual([], results)
        self.assertTrue(issues)


if __name__ == "__main__":
    unittest.main()
